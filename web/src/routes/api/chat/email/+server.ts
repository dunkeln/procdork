import { getAnthropicClient, getAnthropicConfig } from '$lib/server/anthropic/client';
import { json, type RequestHandler } from '@sveltejs/kit';

type Citation = {
	title: string;
	url: string;
	snippet?: string;
	source?: string;
};

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

function parseDraft(text: string) {
	const subject = text.match(/^Subject:\s*(.+)$/im)?.[1]?.trim() ?? 'Supplier quote request';
	const body = text.replace(/^Subject:\s*.+\n?/im, '').trim();

	return { subject, body };
}

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => null);
	const message = typeof body?.message === 'string' ? body.message.trim() : '';
	const prose = typeof body?.prose === 'string' ? body.prose.trim() : '';
	const citations = Array.isArray(body?.citations) ? (body.citations as Citation[]).slice(0, 8) : [];

	if (!message) return json({ error: 'Message is required.' }, { status: 400 });

	let model: string;

	try {
		model = getAnthropicConfig().model;
	} catch {
		return json({ error: 'Anthropic API key or model is not configured.' }, { status: 503 });
	}

	try {
		const response = await getAnthropicClient().messages.create({
			model,
			max_tokens: 900,
			system:
				'Draft concise supplier outreach email text from the provided procurement context. Do not invent supplier facts. Start with a Subject line.',
			messages: [
				{
					role: 'user',
					content: JSON.stringify({
						user_request: message,
						assistant_summary: prose,
						citations
					})
				}
			]
		});

		return json(parseDraft(textFrom(response.content)));
	} catch (error) {
		return json(
			{ error: error instanceof Error ? error.message : 'Email draft failed.' },
			{ status: 500 }
		);
	}
};
