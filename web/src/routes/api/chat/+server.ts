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
	source: 'search' | 'fetch' | 'document';
	retrieved_at?: string;
	document_type?: DocumentType;
	mime_hint?: string;
};

type ChatCitation = Evidence;
type DocumentType = 'coa' | 'sds' | 'spec-sheet' | 'certificate' | 'price-list' | 'other';

type DocumentLink = {
	document_type: DocumentType;
	title: string;
	url: string;
	mime_hint: string;
	retrieved_at: string;
	confidence: 'high' | 'medium' | 'low';
	reason: string;
};

const tools: ToolUnion[] = [
	{
		name: 'tinyfish_search',
		description:
			'Search the live web for supplier procurement evidence, including vendor pages, filings, research, news, and public document URLs such as PDFs for SDS, COA, spec sheets, certificates, and price lists.',
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
			'Fetch clean markdown from known URLs and surface linked supplier documents. Do not rely on this tool to parse PDFs; use it to identify and cite likely SDS, COA, spec sheet, certificate, and price-list file URLs.',
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

function mimeHint(url: string) {
	const path = new URL(url).pathname.toLowerCase();

	if (path.endsWith('.pdf')) return 'application/pdf';
	if (path.endsWith('.doc')) return 'application/msword';
	if (path.endsWith('.docx')) return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
	if (path.endsWith('.xls')) return 'application/vnd.ms-excel';
	if (path.endsWith('.xlsx')) return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
	if (path.endsWith('.csv')) return 'text/csv';
	return 'text/html';
}

function classifyDocument(url: string, title = '', retrieved_at = new Date().toISOString()): DocumentLink | undefined {
	if (!URL.canParse(url)) return undefined;

	const haystack = `${decodeURIComponent(url)} ${title}`.toLowerCase();
	const hasFileExtension = /\.(pdf|docx?|xlsx?|csv)(?:$|[?#])/i.test(url);
	const matches = [
		['coa', /\b(coa|certificate of analysis)\b/i],
		['sds', /\b(sds|msds|safety data sheet)\b/i],
		['spec-sheet', /\b(spec|specification|technical data sheet|tds)\b/i],
		['certificate', /\b(certificate|certification|kosher|halal|organic|iso)\b/i],
		['price-list', /\b(price list|pricing|quote|rfq)\b/i]
	] as const;
	const match = matches.find(([, pattern]) => pattern.test(haystack));

	if (!hasFileExtension && !match) return undefined;

	return {
		document_type: match?.[0] ?? 'other',
		title: title || url,
		url,
		mime_hint: mimeHint(url),
		retrieved_at,
		confidence: match && hasFileExtension ? 'high' : match || hasFileExtension ? 'medium' : 'low',
		reason: match
			? 'Document type inferred from URL, title, or surrounding link text.'
			: 'Document-like file extension found; document type is not named.'
	};
}

function linksFrom(value: unknown) {
	if (typeof value !== 'object' || value === null || !('links' in value)) return [];
	const links = value.links;
	return Array.isArray(links) ? links.filter((link): link is string => typeof link === 'string') : [];
}

function citationsFrom(evidence: Evidence[]): ChatCitation[] {
	const seen = new Set<string>();

	return evidence.filter((item) => {
		if (seen.has(item.url)) return false;
		seen.add(item.url);
		return true;
	});
}

function shouldSuggestEmail(message: string) {
	return /\b(email|outreach|quote|rfq|intro|contact|supplier)\b/i.test(message);
}

function maskedEmail(text: string) {
	const email = text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0];
	if (!email) return '';

	const [user, domain] = email.split('@');
	return `${user.slice(0, Math.min(3, user.length))}...@${domain}`;
}

function supplierName(text: string) {
	const match = text.match(
		/(?:recommend(?:ed)?|best option|best supplier|choose|selected supplier)(?:\s+is|\s*:)?\s+[*_`"]*([A-Z][A-Za-z0-9&.,' -]{2,60})/i
	);
	return match?.[1]?.replace(/[*_`".,]+$/g, '').trim() ?? '';
}

function suggestEmailLabel(message: string, finalText: string, citations: ChatCitation[]) {
	if (!shouldSuggestEmail(message)) return undefined;

	const context = [finalText, message, ...citations.flatMap((item) => [item.title, item.snippet ?? ''])]
		.filter(Boolean)
		.join('\n');
	const supplier = supplierName(context);
	const email = maskedEmail(context);

	if (supplier && email) return `Write email to ${supplier} (${email})`;
	if (supplier) return `Write email to ${supplier}`;
	if (email) return `Write email (${email})`;
	return 'Write email';
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

			const retrieved_at = new Date().toISOString();
			const data = await getTinyFishClient().search.query({
				query,
				location: 'US',
				language: 'en'
			});
			const results = data.results.slice(0, 5);
			const document_links = results
				.map((result) => classifyDocument(result.url, result.title, retrieved_at))
				.filter((document): document is DocumentLink => Boolean(document));

			evidence.push(
				...results.map((result) => ({
					title: result.title,
					url: result.url,
					snippet: result.snippet,
					source: 'search' as const,
					retrieved_at
				})),
				...document_links.map((document) => ({
					title: document.title,
					url: document.url,
					snippet: document.reason,
					source: 'document' as const,
					retrieved_at: document.retrieved_at,
					document_type: document.document_type,
					mime_hint: document.mime_hint
				}))
			);

			return jsonToolResult(toolUse, { results, document_links });
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

			const retrieved_at = new Date().toISOString();
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
			const document_links = data.results
				.flatMap((result) =>
					linksFrom(result).map((link) =>
						classifyDocument(link, result.title ?? result.final_url ?? result.url, retrieved_at)
					)
				)
				.filter((document): document is DocumentLink => Boolean(document))
				.slice(0, 20);

			evidence.push(
				...data.results.map((result) => ({
					title: result.title ?? result.final_url ?? result.url,
					url: result.final_url ?? result.url,
					snippet: result.description ?? undefined,
					source: 'fetch' as const,
					retrieved_at
				})),
				...document_links.map((document) => ({
					title: document.title,
					url: document.url,
					snippet: document.reason,
					source: 'document' as const,
					retrieved_at: document.retrieved_at,
					document_type: document.document_type,
					mime_hint: document.mime_hint
				}))
			);

			return jsonToolResult(toolUse, { results, document_links, errors: data.errors });
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
							'You are a supplier procurement analyst. Use TinyFish tools for current web evidence. Cite source URLs when evidence is used. Treat PDF, spreadsheet, and document links as evidence pointers only unless their contents were explicitly extracted as text. Do not invent facts from filenames.',
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

				const finalMessages: MessageParam[] = [
					...messages,
					{
						role: 'user',
						content:
							'Produce the final answer now as visible markdown prose. Do not draft an outreach email unless the user explicitly asked for email text. If email would be useful, summarize why an email draft can be prepared separately.'
					}
				];
				const finalSystem =
					'You are a supplier procurement analyst. Write final visible markdown prose. Use only available tool evidence. If a requested field is not listed, say "not listed". Do not include a full email draft in this answer.';
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
