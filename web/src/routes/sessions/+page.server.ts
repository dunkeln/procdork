import { listChatSessions } from '$lib/server/storage/chat';
import { redirect } from '@sveltejs/kit';

export async function load() {
	try {
		const [session] = await listChatSessions(1);
		redirect(307, `/sessions/${session?.slug ?? crypto.randomUUID()}`);
	} catch (error) {
		if (error instanceof Error && error.message === 'DATABASE_URL is not configured.') {
			redirect(307, `/sessions/${crypto.randomUUID()}`);
		}

		throw error;
	}
}
