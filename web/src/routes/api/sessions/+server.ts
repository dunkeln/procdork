import { createChatSession } from '$lib/server/storage/chat';
import { json, type RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async () => {
	try {
		return json({ slug: await createChatSession() });
	} catch (error) {
		return json(
			{ error: error instanceof Error ? error.message : 'Session creation failed.' },
			{ status: 503 }
		);
	}
};
