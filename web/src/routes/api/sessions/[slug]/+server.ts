import { deleteChatSession, renameChatSession } from '$lib/server/storage/chat';
import { json, type RequestHandler } from '@sveltejs/kit';

export const PATCH: RequestHandler = async ({ params, request }) => {
	try {
		if (!params.slug) return json({ error: 'Session slug is required.' }, { status: 400 });

		const body = await request.json().catch(() => null);
		const title = typeof body?.title === 'string' ? body.title : '';

		await renameChatSession(params.slug, title);
		return json({ ok: true });
	} catch (error) {
		return json(
			{ error: error instanceof Error ? error.message : 'Session rename failed.' },
			{ status: 503 }
		);
	}
};

export const DELETE: RequestHandler = async ({ params }) => {
	try {
		if (!params.slug) return json({ error: 'Session slug is required.' }, { status: 400 });

		await deleteChatSession(params.slug);
		return json({ ok: true });
	} catch (error) {
		return json(
			{ error: error instanceof Error ? error.message : 'Session deletion failed.' },
			{ status: 503 }
		);
	}
};
