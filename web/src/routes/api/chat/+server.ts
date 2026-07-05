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

function historyFrom(body: unknown): MessageParam[] {
	if (
		typeof body !== 'object' ||
		body === null ||
		!('history' in body) ||
		!Array.isArray(body.history)
	) {
		return [];
	}

	return body.history
		.filter(
			(item): item is { role: 'user' | 'assistant'; content: string } =>
				typeof item === 'object' &&
				item !== null &&
				'role' in item &&
				(item.role === 'user' || item.role === 'assistant') &&
				'content' in item &&
				typeof item.content === 'string' &&
				Boolean(item.content.trim())
		)
		.slice(-6)
		.map((item) => ({
			role: item.role,
			content: item.content.trim().slice(0, 2500)
		}));
}

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => null);
	const message = typeof body?.message === 'string' ? body.message.trim() : '';
	const sessionId =
		typeof body?.sessionId === 'string' && body.sessionId.trim()
			? body.sessionId.trim().slice(0, 120)
			: 'ephemeral';
	const turnId = crypto.randomUUID();

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
			const messages: MessageParam[] = [...historyFrom(body), { role: 'user', content: message }];
			let finalText = '';
			const writeText = (text: string, channel: 'progress' | 'answer') => {
				write({ type: 'delta', channel, text });
			};

			try {
				let answeredWithoutTools = false;

				for (let round = 0; round < 4; round += 1) {
					const response = await anthropic.messages.create({
						model,
						max_tokens: 1200,
						system:
							'You are a supplier procurement analyst. Use tools when current evidence or document-backed extraction is needed. You have web search, web fetch, and document ingestion tools. If search/fetch returns relevant document_links and the user asks for document-backed facts such as MOQ, lead time, grade, COA, SDS, spec, certificate, or price-list details, call document ingestion before finalizing. Before a tool call, you may write a brief visible readout of what you know or why the next tool is needed. Keep interim readouts short. Cite source URLs when evidence is used. Treat PDF, spreadsheet, and document links as evidence pointers unless document ingestion returned extracted claims. Do not invent facts from filenames.',
						messages,
						tools: procurementTools,
						tool_choice: { type: 'auto' }
					});
					const toolUses = toolUsesFrom(response.content);
					const responseText = textFrom(response.content);

					if (!toolUses.length) {
						finalText = responseText;
						if (responseText) writeText(responseText, 'answer');
						answeredWithoutTools = true;
						break;
					}

					if (responseText) writeText(responseText, 'progress');

					messages.push({
						role: 'assistant',
						content: response.content as MessageParam['content']
					});
					const toolResults = [];
					for (const toolUse of toolUses) {
						write({
							type: 'tool',
							name: toolUse.name,
							label: toolLabel(toolUse.name),
							status: 'running'
						});
						const result = await runProcurementTool(toolUse, evidence, { sessionId, turnId });
						write({
							type: 'tool',
							name: toolUse.name,
							label: toolLabel(toolUse.name),
							status: result.is_error ? 'error' : 'done'
						});
						toolResults.push(result);
					}
					messages.push({
						role: 'user',
						content: toolResults
					});
					write({ type: 'evidence', evidence });
				}

				if (!answeredWithoutTools) {
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

					for await (const event of finalStream) {
						const text = streamText(event);
						if (text) {
							finalText += text;
							writeText(text, 'answer');
						}
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
					if (finalText) writeText(finalText, 'answer');
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
