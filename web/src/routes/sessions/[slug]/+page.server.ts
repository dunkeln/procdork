import { listChatSessions, loadSessionMessages } from '$lib/server/storage/chat';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	try {
		const [messages, sessions] = await Promise.all([
			loadSessionMessages(params.slug),
			listChatSessions()
		]);

		return { messages, sessions, persistenceWarning: '' };
	} catch (error) {
		if (error instanceof Error && error.message === 'DATABASE_URL is not configured.') {
			return {
				messages: [],
				sessions: [],
				persistenceWarning: 'DATABASE_URL is not configured; session history is unavailable.'
			};
		}

		throw error;
	}
};
