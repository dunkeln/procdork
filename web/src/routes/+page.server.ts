import { listChatSessions } from '$lib/server/storage/chat';
import { redirect } from '@sveltejs/kit';

export async function load() {
	const [session] = await listChatSessions(1);
	redirect(307, `/sessions/${session?.slug ?? crypto.randomUUID()}`);
}
