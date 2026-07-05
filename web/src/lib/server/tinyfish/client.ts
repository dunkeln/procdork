import { loadDotenv } from '$lib/server/env';
import { TinyFish } from '@tiny-fish/sdk';

let client: TinyFish | undefined;

export function getTinyFishClient() {
	const apiKey = getTinyFishApiKey();

	client ??= new TinyFish({ apiKey });
	return client;
}

export function getTinyFishApiKey() {
	loadDotenv();

	const apiKey = process.env.TINYFISH_API_KEY ?? process.env.TINYFISH;

	if (!apiKey) {
		throw new Error('TinyFish API key is not configured.');
	}

	return apiKey;
}
