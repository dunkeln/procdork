create table if not exists sessions (
	slug text primary key,
	owner_id text null,
	title text null,
	created_at timestamptz not null default now(),
	updated_at timestamptz not null default now()
);

create table if not exists messages (
	id uuid primary key,
	session_slug text not null references sessions(slug) on delete cascade,
	role text not null check (role in ('user', 'assistant')),
	content text not null default '',
	original_request text null,
	suggest_email boolean not null default false,
	suggest_email_label text null,
	metadata jsonb not null default '{}'::jsonb,
	created_at timestamptz not null default now(),
	completed_at timestamptz null
);

create table if not exists message_events (
	id bigserial primary key,
	session_slug text not null references sessions(slug) on delete cascade,
	message_id uuid null references messages(id) on delete set null,
	turn_id uuid null,
	event_type text not null,
	event jsonb not null,
	created_at timestamptz not null default now()
);

create table if not exists sources (
	url text primary key,
	title text not null,
	snippet text null,
	source_kind text not null check (source_kind in ('search', 'fetch', 'document')),
	retrieved_at timestamptz null,
	document_type text null,
	mime_hint text null,
	created_at timestamptz not null default now(),
	updated_at timestamptz not null default now()
);

create table if not exists message_sources (
	message_id uuid not null references messages(id) on delete cascade,
	source_url text not null references sources(url) on delete cascade,
	position integer not null,
	created_at timestamptz not null default now(),
	primary key (message_id, source_url)
);

create table if not exists ingestion_events (
	event_id text primary key,
	event_type text not null,
	schema_version text not null,
	emitted_at timestamptz not null,
	job_id text not null,
	session_id text null,
	turn_id text null,
	status text not null,
	duration_ms bigint not null,
	payload jsonb not null
);

create index if not exists messages_session_created_idx on messages (session_slug, created_at desc);
create index if not exists message_events_session_created_idx on message_events (session_slug, created_at);
create index if not exists message_sources_message_position_idx on message_sources (message_id, position);
create index if not exists sessions_updated_idx on sessions (updated_at desc);
create index if not exists ingestion_events_emitted_idx on ingestion_events (emitted_at desc);
