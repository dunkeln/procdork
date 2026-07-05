import { getAnthropicClient, getAnthropicConfig } from '$lib/server/anthropic/client';
import { streamText, textFrom } from '$lib/server/anthropic/messages';
import { shouldSuggestEmail, suggestEmailLabel } from '$lib/server/chat/email-suggestion';
import {
	citationsFrom,
	procurementTools,
	runProcurementTool,
	toolLabel,
	type Evidence
} from '$lib/server/tinyfish/procurement-tools';
import { json, type RequestHandler } from '@sveltejs/kit';
import type { MessageParam, ToolUseBlock } from '@anthropic-ai/sdk/resources/messages';

function ndjson(event: unknown) {
	return `${JSON.stringify(event)}\n`;
}

function toolUsesFrom(content: unknown[]) {
	return content.filter(
		(block): block is ToolUseBlock =>
			typeof block === 'object' && block !== null && 'type' in block && block.type === 'tool_use'
	);
}

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => null);
	const message = typeof body?.message === 'string' ? body.message.trim() : '';

	if (!message) {
		return json({ error: 'Message is required.' }, { status: 400 });
	}

	if (message.length > 1000) {
		return json({ error: 'Message must be 1000 characters or fewer.' }, { status: 400 });
	}

	let model: string;

	try {
		model = getAnthropicConfig().model;
	} catch {
		return json({ error: 'Anthropic API key or model is not configured.' }, { status: 503 });
	}

	const stream = new ReadableStream({
		async start(controller) {
			const encoder = new TextEncoder();
			const write = (event: unknown) => controller.enqueue(encoder.encode(ndjson(event)));
			const anthropic = getAnthropicClient();
			const evidence: Evidence[] = [];
			const messages: MessageParam[] = [{ role: 'user', content: message }];

			try {
				for (let round = 0; round < 2; round += 1) {
					const response = await anthropic.messages.create({
						model,
						max_tokens: 1200,
						system:
							'You are a supplier procurement analyst. Use TinyFish tools for current web evidence. Cite source URLs when evidence is used. Treat PDF, spreadsheet, and document links as evidence pointers only unless their contents were explicitly extracted as text. Do not invent facts from filenames.',
						messages,
						tools: procurementTools,
						tool_choice: { type: 'auto' }
					});
					const toolUses = toolUsesFrom(response.content);

					if (!toolUses.length) {
						const text = textFrom(response.content);
						if (text) write({ type: 'delta', text });
						break;
					}

					messages.push({
						role: 'assistant',
						content: response.content as MessageParam['content']
					});
					const toolResults = await Promise.all(
						toolUses.map(async (toolUse) => {
							write({
								type: 'tool',
								name: toolUse.name,
								label: toolLabel(toolUse.name),
								status: 'running'
							});
							const result = await runProcurementTool(toolUse, evidence);
							write({
								type: 'tool',
								name: toolUse.name,
								label: toolLabel(toolUse.name),
								status: result.is_error ? 'error' : 'done'
							});
							return result;
						})
					);
					messages.push({
						role: 'user',
						content: toolResults
					});
					write({ type: 'evidence', evidence });
				}

				const finalMessages: MessageParam[] = [
					...messages,
					{
						role: 'user',
						content:
							'Produce the final answer now as visible markdown. Preserve material findings, but reduce parsing load: open with one decision/readout sentence, use a compact markdown table when comparing suppliers, keep gaps visible as "not listed", "not found", or "document found, not parsed", and use inline citation markers like [1], [2] next to source-backed claims. Do not draft an outreach email unless the user explicitly asked for email text.'
					}
				];
				const finalSystem =
					'You are a supplier procurement analyst. Write like an operator handoff, not a report. Start with the answer. Do not restate the task or methodology. Use short scan-first sections only when useful. Use compact markdown tables for supplier comparisons. Put unknowns directly in the relevant row or sentence as "not listed" or "not found". Mention supplier documents as "document found, not parsed" unless contents were extracted as text. Use inline citation markers [1], [2], etc. beside claims that use evidence; match those markers to the citation order returned by the tool context when possible. Do not include a full email draft in this answer.';
				const finalStream = await anthropic.messages.create({
					model,
					max_tokens: 2000,
					system: finalSystem,
					messages: finalMessages,
					stream: true
				});

				let finalText = '';
				for await (const event of finalStream) {
					const text = streamText(event);
					if (text) {
						finalText += text;
						write({ type: 'delta', text });
					}
				}
				if (!finalText.trim()) {
					const finalResponse = await anthropic.messages.create({
						model,
						max_tokens: 2000,
						system:
							'You are a supplier procurement analyst. Write visible concise markdown text. Do not return only thinking.',
						messages: [
							...messages,
							{
								role: 'user',
								content:
									'Now produce the final visible markdown answer from the available tool results. Do not use tools.'
							}
						]
					});
					finalText = textFrom(finalResponse.content);
					if (finalText) write({ type: 'delta', text: finalText });
				}

				const citations = citationsFrom(evidence);
				write({
					type: 'final',
					prose: finalText,
					citations,
					suggestEmail: shouldSuggestEmail(message),
					suggestEmailLabel: suggestEmailLabel(message, finalText, citations)
				});
				write({ type: 'evidence', evidence: citations });
				write({ type: 'done' });
			} catch (error) {
				write({
					type: 'error',
					error: error instanceof Error ? error.message : 'Chat runtime failed.'
				});
			} finally {
				controller.close();
			}
		}
	});

	return new Response(stream, {
		headers: {
			'cache-control': 'no-cache',
			'content-type': 'application/x-ndjson'
		}
	});
};
