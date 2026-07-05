import { getTinyFishClient } from '$lib/server/tinyfish/client';
import { createIngestionJob, normalizeIngestionSource } from '$lib/server/ingestion/client';
import { FetchFormat } from '@tiny-fish/sdk';
import type {
	ToolResultBlockParam,
	ToolUnion,
	ToolUseBlock
} from '@anthropic-ai/sdk/resources/messages';
import type { DocumentIngestionRequest } from '$lib/contracts/supplier-entity';

type DocumentType = 'coa' | 'sds' | 'spec-sheet' | 'certificate' | 'price-list' | 'quote' | 'other';

export type Evidence = {
	title: string;
	url: string;
	snippet?: string;
	source: 'search' | 'fetch' | 'document';
	retrieved_at?: string;
	document_type?: DocumentType;
	mime_hint?: string;
};

export type ChatCitation = Evidence;

type DocumentLink = {
	document_type: DocumentType;
	title: string;
	url: string;
	mime_hint: string;
	retrieved_at: string;
	confidence: 'high' | 'medium' | 'low';
	reason: string;
};

type ToolContext = {
	sessionId: string;
	turnId?: string;
};

export const procurementTools: ToolUnion[] = [
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
	},
	{
		name: 'ingest_documents',
		description:
			'Parse document pointers already discovered by web search/fetch when the user needs document-backed supplier facts such as MOQ, lead time, grade, COA/SDS/spec/certificate details, or conflicts. Call this after search/fetch returns relevant document_links for those facts. If documents are omitted, ingest currently discovered document evidence.',
		input_schema: {
			type: 'object',
			properties: {
				documents: {
					type: 'array',
					items: {
						type: 'object',
						properties: {
							url: { type: 'string', description: 'Absolute public document URL.' },
							title: { type: 'string', description: 'Document title or link text.' },
							document_type: {
								type: 'string',
								description:
									'Best known document kind: coa, sds, spec-sheet, certificate, price-list, quote, or other.'
							},
							mime_hint: { type: 'string', description: 'MIME hint such as application/pdf.' },
							retrieved_at: { type: 'string', description: 'ISO retrieval timestamp if known.' },
							reason: {
								type: 'string',
								description: 'Why this document is relevant to the procurement question.'
							}
						},
						required: ['url']
					},
					description: 'Document pointers to ingest. Up to 5 URLs.'
				}
			}
		}
	}
];

export function toolLabel(name: string) {
	if (name === 'tinyfish_fetch') return 'web fetch';
	if (name === 'ingest_documents') return 'document ingest';
	return 'web search';
}

export function citationsFrom(evidence: Evidence[]): ChatCitation[] {
	const seen = new Set<string>();

	return evidence.filter((item) => {
		if (seen.has(item.url)) return false;
		seen.add(item.url);
		return true;
	});
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

function mimeHint(url: string) {
	const path = new URL(url).pathname.toLowerCase();

	if (path.endsWith('.pdf')) return 'application/pdf';
	if (path.endsWith('.doc')) return 'application/msword';
	if (path.endsWith('.docx'))
		return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
	if (path.endsWith('.xls')) return 'application/vnd.ms-excel';
	if (path.endsWith('.xlsx'))
		return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
	if (path.endsWith('.csv')) return 'text/csv';
	return 'text/html';
}

function classifyDocument(
	url: string,
	title = '',
	retrieved_at = new Date().toISOString()
): DocumentLink | undefined {
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
	return Array.isArray(links)
		? links.filter((link): link is string => typeof link === 'string')
		: [];
}

export async function runProcurementTool(
	toolUse: ToolUseBlock,
	evidence: Evidence[],
	context: ToolContext
) {
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

		if (toolUse.name === 'ingest_documents') {
			const explicitDocuments =
				typeof toolUse.input === 'object' &&
				toolUse.input &&
				'documents' in toolUse.input &&
				Array.isArray(toolUse.input.documents)
					? toolUse.input.documents
					: [];
			const fallbackDocuments = evidence
				.filter((item) => item.source === 'document')
				.map((item) => ({
					url: item.url,
					title: item.title,
					document_type: item.document_type,
					mime_hint: item.mime_hint,
					retrieved_at: item.retrieved_at,
					reason: item.snippet
				}));
			const sources = dedupeSources(
				(explicitDocuments.length ? explicitDocuments : fallbackDocuments)
					.map((document) =>
						typeof document === 'object' && document !== null
							? normalizeIngestionSource(document)
							: undefined
					)
					.filter((source): source is DocumentIngestionRequest => Boolean(source))
			).slice(0, 5);

			if (!sources.length) {
				return jsonToolResult(
					toolUse,
					{ error: 'No document pointers are available to ingest.' },
					true
				);
			}

			const job = await createIngestionJob({
				sessionId: context.sessionId,
				turnId: context.turnId,
				sources
			});

			return jsonToolResult(toolUse, {
				job_id: job.job_id,
				status: job.status,
				result: job.result,
				error: job.error
			});
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

function dedupeSources(sources: DocumentIngestionRequest[]) {
	const seen = new Set<string>();

	return sources.filter((source) => {
		const key = source.url ?? source.source_id;
		if (seen.has(key)) return false;
		seen.add(key);
		return true;
	});
}
