import { loadDotenv } from '$lib/server/env';
import { createHash } from 'node:crypto';
import { documentIngestionRequestSchema } from '$lib/contracts/supplier-entity';
import type { ArtifactType, DocumentIngestionRequest } from '$lib/contracts/supplier-entity';
import { saveIngestionEvent, type DurableIngestionEvent } from '$lib/server/storage/ingestion';

type IngestionJob = {
	job_id: string;
	status: 'queued' | 'running' | 'succeeded' | 'failed' | 'partial';
	result?: unknown;
	error?: string | null;
	event?: DurableIngestionEvent | null;
};

const INGESTION_TIMEOUT_MS = 45_000;

export function getIngestionServiceUrl() {
	loadDotenv();
	return (
		process.env.INGESTION_SERVICE_URL ??
		process.env.DOCUMENT_INGESTION_URL ??
		process.env.INGESTION_URL ??
		vercelIngestionServiceUrl()
	);
}

function ingestionUrl(path: string, serviceUrl: string) {
	const url = new URL(serviceUrl);
	url.pathname = `${url.pathname.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
	return url;
}

function vercelIngestionServiceUrl() {
	const host = process.env.VERCEL_URL ?? process.env.VERCEL_PROJECT_PRODUCTION_URL;
	return host ? `https://${host}/svc/ingestion` : undefined;
}

export function sourceIdFor(url: string) {
	return `src_${createHash('sha1').update(url).digest('hex').slice(0, 12)}`;
}

export function normalizeIngestionSource(source: {
	url?: string;
	title?: string;
	artifact_type?: string;
	document_type?: string;
	mime_hint?: string;
	retrieved_at?: string;
	reason?: string;
}): DocumentIngestionRequest | undefined {
	const url = typeof source.url === 'string' && URL.canParse(source.url) ? source.url : undefined;
	if (!url) return undefined;

	const artifact_type = normalizeArtifactType(source.artifact_type ?? source.document_type);
	const request = {
		source_id: sourceIdFor(url),
		artifact_type,
		url,
		mime_hint: source.mime_hint,
		title: source.title || url,
		retrieved_at: source.retrieved_at ?? new Date().toISOString(),
		reason: source.reason ?? `Document pointer classified as ${artifact_type}.`
	};

	return documentIngestionRequestSchema.parse(request);
}

export async function createIngestionJob(input: {
	sessionId: string;
	sources: DocumentIngestionRequest[];
	turnId?: string;
}) {
	const serviceUrl = getIngestionServiceUrl();
	if (!serviceUrl) throw new Error('Document ingestion service URL is not configured.');

	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), INGESTION_TIMEOUT_MS);

	try {
		const response = await fetch(ingestionUrl('/ingestion/jobs', serviceUrl), {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({
				session_id: input.sessionId,
				turn_id: input.turnId,
				sources: input.sources
			}),
			signal: controller.signal
		});
		const data = (await response.json().catch(() => null)) as
			IngestionJob | { error?: string } | null;

		if (!response.ok) {
			throw new Error(
				data && 'error' in data && data.error ? data.error : 'Document ingestion failed.'
			);
		}

		const job = data as IngestionJob;
		if (!job.event) throw new Error('Document ingestion returned no durable completion event.');
		await saveIngestionEvent(job.event);
		return job;
	} finally {
		clearTimeout(timeout);
	}
}

function normalizeArtifactType(value?: string): ArtifactType {
	const normalized = value?.trim().toLowerCase();
	if (
		normalized === 'coa' ||
		normalized === 'sds' ||
		normalized === 'spec-sheet' ||
		normalized === 'certificate' ||
		normalized === 'price-list' ||
		normalized === 'quote' ||
		normalized === 'supplier-questionnaire'
	) {
		return normalized;
	}
	return 'other';
}
