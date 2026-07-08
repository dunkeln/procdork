import { createChatSession } from '$lib/server/storage/chat';
import { json, type RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
	try {
		const body = await request.json().catch(() => null);
		const title = typeof body?.title === 'string' ? body.title : undefined;

		return json({ slug: await createChatSession(title) });
	} catch (error) {
		return json(
			{ error: error instanceof Error ? error.message : 'Session creation failed.' },
			{ status: 503 }
		);
	}
};
