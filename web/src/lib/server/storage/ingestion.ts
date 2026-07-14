import { database, ensureStorageSchema } from './database';

export type DurableIngestionEvent = {
	event_id: string;
	event_type: string;
	schema_version: string;
	emitted_at: string;
	job_id: string;
	session_id?: string | null;
	turn_id?: string | null;
	status: string;
	duration_ms: number;
	sources: unknown[];
	observed_suppliers: unknown[];
	canonical_suppliers: unknown[];
	source_claims: unknown[];
	conflicts: unknown[];
	artifacts: unknown[];
};

export async function saveIngestionEvent(event: DurableIngestionEvent) {
	await ensureStorageSchema();
	await database().query(
		`
			insert into ingestion_events (
				event_id, event_type, schema_version, emitted_at, job_id,
				session_id, turn_id, status, duration_ms, payload
			)
			values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
			on conflict (event_id) do nothing
		`,
		[
			event.event_id,
			event.event_type,
			event.schema_version,
			event.emitted_at,
			event.job_id,
			event.session_id ?? null,
			event.turn_id ?? null,
			event.status,
			event.duration_ms,
			JSON.stringify(event)
		]
	);
}
