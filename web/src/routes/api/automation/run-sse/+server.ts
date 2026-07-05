import { getTinyFishClient } from '$lib/server/tinyfish/client';
import { BrowserProfile } from '@tiny-fish/sdk';
import { json, type RequestHandler } from '@sveltejs/kit';

function sse(event: unknown) {
	return `data: ${JSON.stringify(event)}\n\n`;
}

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => null);
	const url = typeof body?.url === 'string' ? body.url.trim() : '';
	const goal = typeof body?.goal === 'string' ? body.goal.trim() : '';

	if (!url || !goal) {
		return json({ error: 'Automation url and goal are required.' }, { status: 400 });
	}

	try {
		new URL(url);
	} catch {
		return json({ error: 'Automation url must be absolute.' }, { status: 400 });
	}

	const stream = new ReadableStream({
		async start(controller) {
			const encoder = new TextEncoder();

			try {
				const agentStream = await getTinyFishClient().agent.stream({
					url,
					goal,
					browser_profile: BrowserProfile.LITE
				});

				for await (const event of agentStream) {
					controller.enqueue(encoder.encode(sse(event)));
				}
			} catch (error) {
				controller.enqueue(
					encoder.encode(
						sse({
							type: 'ERROR',
							error: error instanceof Error ? error.message : 'TinyFish automation failed.'
						})
					)
				);
			} finally {
				controller.close();
			}
		}
	});

	return new Response(stream, {
		headers: {
			'cache-control': 'no-cache',
			'content-type': 'text/event-stream'
		}
	});
};
