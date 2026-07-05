import { getTinyFishApiKey } from '$lib/server/tinyfish/client';
import { json, type RequestHandler } from '@sveltejs/kit';

const domainTypes = new Set(['web', 'news', 'research_paper']);

export const POST: RequestHandler = async ({ request, fetch }) => {
	const body = await request.json().catch(() => null);
	const query = typeof body?.query === 'string' ? body.query.trim() : '';
	const domainType = typeof body?.domainType === 'string' ? body.domainType : 'web';

	if (!query) {
		return json({ error: 'Search query is required.' }, { status: 400 });
	}

	if (query.length > 500) {
		return json({ error: 'Search query must be 500 characters or fewer.' }, { status: 400 });
	}

	if (!domainTypes.has(domainType)) {
		return json({ error: 'Unsupported search type.' }, { status: 400 });
	}

	let apiKey: string;

	try {
		apiKey = getTinyFishApiKey();
	} catch {
		return json({ error: 'TinyFish API key is not configured.' }, { status: 503 });
	}

	const params = new URLSearchParams({
		query,
		domain_type: domainType,
		location: 'US',
		language: 'en'
	});

	const response = await fetch(`https://api.search.tinyfish.ai?${params}`, {
		headers: {
			'X-API-Key': apiKey
		}
	});

	const data = await response.json().catch(() => null);

	if (!response.ok) {
		return json(
			{ error: data?.error ?? `TinyFish search failed with ${response.status}.` },
			{ status: response.status }
		);
	}

	return json(data);
};
