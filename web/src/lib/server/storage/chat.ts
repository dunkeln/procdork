import { loadDotenv } from '$lib/server/env';
import { neon } from '@neondatabase/serverless';
import schemaSql from './schema.sql?raw';
import type { ChatCitation } from '$lib/server/tinyfish/procurement-tools';
import type { MessageParam } from '@anthropic-ai/sdk/resources/messages';

type Db = ReturnType<typeof neon>;
const PROMPT_HISTORY_LIMIT = 10;

export type StoredChatMessage = {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	originalRequest?: string;
	evidence?: ChatCitation[];
	suggestEmail?: boolean;
	suggestEmailLabel?: string;
};

export type StoredChatSession = {
	slug: string;
	title: string;
	updatedAt: string;
	messageCount: number;
};

let db: Db | undefined;
let init: Promise<void> | undefined;

function sql() {
	loadDotenv();
	const databaseUrl = process.env.DATABASE_URL;
	if (!databaseUrl) throw new Error('DATABASE_URL is not configured.');

	db ??= neon(databaseUrl);
	return db;
}

function normalizeSlug(slug: string) {
	return slug.trim().slice(0, 120) || 'ephemeral';
}

function titleFromMessage(message: string) {
	const compact = message.replace(/\s+/g, ' ').trim();
	return compact.length > 64 ? `${compact.slice(0, 61)}...` : compact || null;
}

export async function ensureChatSchema() {
	const client = sql();
	init ??= (async () => {
		for (const statement of schemaSql
			.split(/;\s*\n/)
			.map((item) => item.trim())
			.filter(Boolean)) {
			await client.query(statement);
		}
	})();
	return init;
}

export async function createChatSession(title?: string) {
	await ensureChatSchema();
	const slug = crypto.randomUUID();

	await sql().query('insert into sessions (slug, title) values ($1, $2)', [
		slug,
		titleFromMessage(title ?? '')
	]);
	return slug;
}

export async function deleteChatSession(sessionSlug: string) {
	await ensureChatSchema();
	await sql().query('delete from sessions where slug = $1', [normalizeSlug(sessionSlug)]);
}

export async function renameChatSession(sessionSlug: string, title: string) {
	await ensureChatSchema();
	await sql().query('update sessions set title = $1, updated_at = now() where slug = $2', [
		titleFromMessage(title),
		normalizeSlug(sessionSlug)
	]);
}

export async function listChatSessions(limit = 40): Promise<StoredChatSession[]> {
	await ensureChatSchema();
	const rows = (await sql().query(
		`
			select
				s.slug,
				coalesce(s.title, 'Untitled chat') as title,
				s.updated_at,
				count(m.id)::int as message_count
			from sessions s
			left join messages m on m.session_slug = s.slug
			group by s.slug
			order by s.updated_at desc
			limit $1
		`,
		[limit]
	)) as Array<{
		slug: string;
		title: string;
		updated_at: string;
		message_count: number;
	}>;

	return rows.map((row) => ({
		slug: row.slug,
		title: row.title,
		updatedAt: row.updated_at,
		messageCount: row.message_count
	}));
}

export async function loadPromptHistory(sessionSlug: string): Promise<MessageParam[]> {
	await ensureChatSchema();
	const rows = (await sql().query(
		`
			select role, content
			from messages
			where session_slug = $1 and (role = 'user' or completed_at is not null) and content <> ''
			order by created_at desc, case role when 'assistant' then 0 else 1 end, id desc
			limit $2
		`,
		[normalizeSlug(sessionSlug), PROMPT_HISTORY_LIMIT]
	)) as { role: 'user' | 'assistant'; content: string }[];

	return rows.reverse().map((row) => ({ role: row.role, content: row.content.slice(0, 2500) }));
}

export async function loadSessionMessages(sessionSlug: string): Promise<StoredChatMessage[]> {
	await ensureChatSchema();
	const rows = (await sql().query(
		`
			select
				m.id,
				m.role,
				m.content,
				m.original_request,
				m.suggest_email,
				m.suggest_email_label,
				coalesce(
					jsonb_agg(
						jsonb_build_object(
							'title', s.title,
							'url', s.url,
							'snippet', s.snippet,
							'source', s.source_kind,
							'retrieved_at', s.retrieved_at,
							'document_type', s.document_type,
							'mime_hint', s.mime_hint
						)
						order by ms.position
					) filter (where s.url is not null),
					'[]'::jsonb
				) as evidence
			from messages m
			left join message_sources ms on ms.message_id = m.id
			left join sources s on s.url = ms.source_url
			where m.session_slug = $1 and (m.role = 'user' or m.content <> '')
			group by m.id
			order by m.created_at desc, case m.role when 'user' then 0 else 1 end
			limit 50
		`,
		[normalizeSlug(sessionSlug)]
	)) as Array<{
		id: string;
		role: 'user' | 'assistant';
		content: string;
		original_request: string | null;
		evidence: ChatCitation[];
		suggest_email: boolean;
		suggest_email_label: string | null;
	}>;

	return rows.map((row) => ({
		id: row.id,
		role: row.role,
		content: row.content,
		...(row.original_request ? { originalRequest: row.original_request } : {}),
		...(row.evidence.length ? { evidence: row.evidence } : {}),
		...(row.suggest_email ? { suggestEmail: true } : {}),
		...(row.suggest_email_label ? { suggestEmailLabel: row.suggest_email_label } : {})
	}));
}

export async function startChatTurn(input: {
	sessionSlug: string;
	turnId: string;
	userMessageId: string;
	assistantMessageId: string;
	message: string;
}) {
	await ensureChatSchema();
	const sessionSlug = normalizeSlug(input.sessionSlug);
	const title = titleFromMessage(input.message);
	await sql().transaction((txn) => [
		txn`
			insert into sessions (slug, title, updated_at)
			values (${sessionSlug}, ${title}, now())
			on conflict (slug) do update set
				title = case
					when sessions.title is null or sessions.title = 'Untitled chat' then excluded.title
					else sessions.title
				end,
				updated_at = excluded.updated_at
		`,
		txn`
			insert into messages (id, session_slug, role, content)
			values (${input.userMessageId}, ${sessionSlug}, 'user', ${input.message})
			on conflict (id) do nothing
		`,
		txn`
			insert into messages (id, session_slug, role, original_request)
			values (${input.assistantMessageId}, ${sessionSlug}, 'assistant', ${input.message})
			on conflict (id) do nothing
		`,
		txn`
			insert into message_events (session_slug, message_id, turn_id, event_type, event)
			values (
				${sessionSlug},
				${input.userMessageId},
				${input.turnId},
				'user_message',
				${JSON.stringify({ type: 'user_message', text: input.message })}::jsonb
			)
		`
	]);
}

export async function saveMessageEvent(input: {
	sessionSlug: string;
	messageId?: string;
	turnId: string;
	event: Record<string, unknown>;
}) {
	await ensureChatSchema();
	const sessionSlug = normalizeSlug(input.sessionSlug);
	const answerDelta =
		input.messageId &&
		input.event.type === 'delta' &&
		input.event.channel !== 'progress' &&
		typeof input.event.text === 'string'
			? input.event.text
			: '';
	await sql().transaction((txn) => [
		txn`
			insert into message_events (session_slug, message_id, turn_id, event_type, event)
			values (
				${sessionSlug},
				${input.messageId ?? null},
				${input.turnId},
				${String(input.event.type ?? 'event')},
				${JSON.stringify(input.event)}::jsonb
			)
		`,
		...(answerDelta
			? [
					txn`
						update messages
						set content = content || ${answerDelta}
						where id = ${input.messageId} and session_slug = ${sessionSlug} and role = 'assistant'
					`
				]
			: []),
		txn`update sessions set updated_at = now() where slug = ${sessionSlug}`
	]);
}

export async function completeAssistantMessage(input: {
	sessionSlug: string;
	messageId: string;
	content: string;
	citations: ChatCitation[];
	suggestEmail: boolean;
	suggestEmailLabel?: string;
}) {
	await ensureChatSchema();
	const sessionSlug = normalizeSlug(input.sessionSlug);
	await sql().transaction((txn) => [
		txn`
			update messages
			set
				content = ${input.content},
				suggest_email = ${input.suggestEmail},
				suggest_email_label = ${input.suggestEmailLabel ?? null},
				completed_at = now()
			where id = ${input.messageId} and session_slug = ${sessionSlug}
		`,
		txn`update sessions set updated_at = now() where slug = ${sessionSlug}`
	]);
	await saveSourcesForMessage(input.messageId, input.citations);
}

async function saveSourcesForMessage(messageId: string, citations: ChatCitation[]) {
	if (!citations.length) return;

	const client = sql();
	for (const [position, citation] of citations.entries()) {
		await client.transaction((txn) => [
			txn`
				insert into sources (
					url,
					title,
					snippet,
					source_kind,
					retrieved_at,
					document_type,
					mime_hint,
					updated_at
				)
				values (
					${citation.url},
					${citation.title},
					${citation.snippet ?? null},
					${citation.source},
					${citation.retrieved_at ?? null},
					${citation.document_type ?? null},
					${citation.mime_hint ?? null},
					now()
				)
				on conflict (url) do update set
					title = excluded.title,
					snippet = excluded.snippet,
					source_kind = excluded.source_kind,
					retrieved_at = excluded.retrieved_at,
					document_type = excluded.document_type,
					mime_hint = excluded.mime_hint,
					updated_at = excluded.updated_at
			`,
			txn`
				insert into message_sources (message_id, source_url, position)
				values (${messageId}, ${citation.url}, ${position})
				on conflict (message_id, source_url) do update set position = excluded.position
			`
		]);
	}
}
