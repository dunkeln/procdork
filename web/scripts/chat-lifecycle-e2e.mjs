const baseUrl = process.env.CHAT_E2E_BASE_URL ?? 'http://127.0.0.1:5173';
const prompt =
	process.env.CHAT_E2E_PROMPT ??
	'Find US suppliers for bulk citric acid USP grade, include any document-backed MOQ or lead-time evidence if available.';
const expectIngestion = process.env.CHAT_E2E_EXPECT_INGESTION === '1';

const response = await fetch(new URL('/api/chat', baseUrl), {
	method: 'POST',
	headers: { 'content-type': 'application/json' },
	body: JSON.stringify({
		message: prompt,
		sessionId: `e2e-${Date.now()}`
	})
});

if (!response.ok) {
	const body = await response.text();
	throw new Error(`chat endpoint failed: ${response.status} ${body}`);
}

if (!response.body) throw new Error('chat endpoint did not return a stream');

const events = [];
const tools = new Set();
let buffer = '';

for await (const chunk of response.body) {
	buffer += Buffer.from(chunk).toString('utf8');
	const lines = buffer.split('\n');
	buffer = lines.pop() ?? '';

	for (const line of lines) {
		if (!line.trim()) continue;
		const event = JSON.parse(line);
		events.push(event);
		if (event.type === 'tool' && event.status === 'done') tools.add(event.name);
	}
}

if (buffer.trim()) events.push(JSON.parse(buffer));

const sawDelta = events.some((event) => event.type === 'delta' && event.text);
const sawAnswerDelta = events.some(
	(event) => event.type === 'delta' && event.channel === 'answer' && event.text
);
const sawUnknownDeltaChannel = events.some(
	(event) => event.type === 'delta' && event.channel !== 'progress' && event.channel !== 'answer'
);
const final = events.find((event) => event.type === 'final');
const sawDone = events.some((event) => event.type === 'done');

if (!sawDelta) throw new Error('expected at least one streamed prose delta');
if (!sawAnswerDelta) throw new Error('expected at least one answer-channel delta');
if (sawUnknownDeltaChannel) throw new Error('delta event used an unknown channel');
if (!final) throw new Error('expected final compiled message event');
if (typeof final.prose !== 'string' || !final.prose.trim()) {
	throw new Error('final event did not include prose');
}
if (!Array.isArray(final.citations)) throw new Error('final event did not include citations array');
if (typeof final.suggestEmail !== 'boolean')
	throw new Error('final event did not include suggestEmail');
if (!sawDone) throw new Error('expected done event');
if (expectIngestion && !tools.has('ingest_documents')) {
	throw new Error('expected document ingestion tool to complete');
}

console.log(
	JSON.stringify(
		{
			ok: true,
			events: events.length,
			tools: [...tools],
			citations: final.citations.length,
			prose_chars: final.prose.length
		},
		null,
		2
	)
);
