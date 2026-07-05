import { getAnthropicClient, getAnthropicConfig } from '$lib/server/anthropic/client';
import { getTinyFishClient } from '$lib/server/tinyfish/client';
import { FetchFormat } from '@tiny-fish/sdk';
import { json, type RequestHandler } from '@sveltejs/kit';
import type {
	MessageParam,
	RawMessageStreamEvent,
	ToolResultBlockParam,
	ToolUnion,
	ToolUseBlock
} from '@anthropic-ai/sdk/resources/messages';

type Evidence = {
	title: string;
	url: string;
	snippet?: string;
	source: 'search' | 'fetch';
};

const tools: ToolUnion[] = [
	{
		name: 'tinyfish_search',
		description:
			'Search the live web for supplier procurement evidence, including vendor pages, filings, research, and news.',
		input_schema: {
			type: 'object',
			properties: {
				query: { type: 'string', description: 'Search query for supplier procurement evidence.' }
			},
			required: ['query']
		}
	},
	{
		name: 'tinyfish_fetch',
		description:
			'Fetch clean markdown from known URLs when supplier evidence needs source details. Use URLs from search results.',
		input_schema: {
			type: 'object',
			properties: {
				urls: {
					type: 'array',
					items: { type: 'string' },
					description: 'Absolute URLs to fetch. Up to 10 URLs.'
				}
			},
			required: ['urls']
		}
	}
];

function ndjson(event: unknown) {
	return `${JSON.stringify(event)}\n`;
}

function streamText(event: RawMessageStreamEvent) {
	return event.type === 'content_block_delta' &&
		event.delta.type === 'text_delta' &&
		typeof event.delta.text === 'string'
		? event.delta.text
		: '';
}

function toolUsesFrom(content: unknown[]) {
	return content.filter(
		(block): block is ToolUseBlock =>
			typeof block === 'object' && block !== null && 'type' in block && block.type === 'tool_use'
	);
}

function textFrom(content: unknown[]) {
	return content
		.map((block) =>
			typeof block === 'object' &&
			block !== null &&
			'type' in block &&
			block.type === 'text' &&
			'text' in block &&
			typeof block.text === 'string'
				? block.text
				: ''
		)
		.join('');
}

function jsonToolResult(
	toolUse: ToolUseBlock,
	content: unknown,
	is_error = false
): ToolResultBlockParam {
	return {
		type: 'tool_result',
		tool_use_id: toolUse.id,
		is_error,
		content: JSON.stringify(content)
	};
}

function toolLabel(name: string) {
	return name === 'tinyfish_fetch' ? 'TinyFish fetch' : 'TinyFish search';
}

async function runTool(toolUse: ToolUseBlock, evidence: Evidence[]) {
	try {
		if (toolUse.name === 'tinyfish_search') {
			const query =
				typeof toolUse.input === 'object' &&
				toolUse.input &&
				'query' in toolUse.input &&
				typeof toolUse.input.query === 'string'
					? toolUse.input.query.trim()
					: '';

			if (!query) return jsonToolResult(toolUse, { error: 'query is required' }, true);

			const data = await getTinyFishClient().search.query({
				query,
				location: 'US',
				language: 'en'
			});
			const results = data.results.slice(0, 5);

			evidence.push(
				...results.map((result) => ({
					title: result.title,
					url: result.url,
					snippet: result.snippet,
					source: 'search' as const
				}))
			);

			return jsonToolResult(toolUse, { results });
		}

		if (toolUse.name === 'tinyfish_fetch') {
			const urls =
				typeof toolUse.input === 'object' &&
				toolUse.input &&
				'urls' in toolUse.input &&
				Array.isArray(toolUse.input.urls)
					? toolUse.input.urls
							.filter((url): url is string => typeof url === 'string')
							.map((url) => url.trim())
							.filter((url) => URL.canParse(url))
							.slice(0, 10)
					: [];

			if (!urls.length)
				return jsonToolResult(toolUse, { error: 'absolute urls are required' }, true);

			const data = await getTinyFishClient().fetch.getContents({
				urls,
				format: FetchFormat.Markdown,
				links: true,
				image_links: false
			});
			const results = data.results.map((result) => ({
				...result,
				text: typeof result.text === 'string' ? result.text.slice(0, 4000) : result.text
			}));

			evidence.push(
				...data.results.map((result) => ({
					title: result.title ?? result.final_url ?? result.url,
					url: result.final_url ?? result.url,
					snippet: result.description ?? undefined,
					source: 'fetch' as const
				}))
			);

			return jsonToolResult(toolUse, { results, errors: data.errors });
		}

		return jsonToolResult(toolUse, { error: `Unknown tool: ${toolUse.name}` }, true);
	} catch (error) {
		return jsonToolResult(
			toolUse,
			{ error: error instanceof Error ? error.message : 'Tool execution failed.' },
			true
		);
	}
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
							'You are a supplier procurement analyst. Use TinyFish tools for current web evidence. Cite source URLs when evidence is used.',
						messages,
						tools,
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
							const result = await runTool(toolUse, evidence);
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

				let finalResponse = await anthropic.messages.create({
					model,
					max_tokens: 2000,
					system:
						'You are a supplier procurement analyst. Write the final visible markdown answer now. Use only available tool evidence. If a requested lead time is not listed, say "not listed" and do not say you need to search more.',
					messages: [
						...messages,
						{
							role: 'user',
							content:
								'Produce the final answer now: compare the distributors against the 5-day baseline, choose the best option from available evidence, and draft the outreach email. Do not mention future searching.'
						}
					]
				});

				let finalText = textFrom(finalResponse.content);
				if (!finalText.trim()) {
					finalResponse = await anthropic.messages.create({
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
				}
				if (finalText) write({ type: 'delta', text: finalText });

				write({ type: 'evidence', evidence });
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
