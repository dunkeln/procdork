import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { TinyFish } from '@tiny-fish/sdk';
import { config } from 'dotenv';

let client: TinyFish | undefined;
let envLoaded = false;

function findDotenv(start = process.cwd()) {
	let current = start;

	while (true) {
		const candidate = join(current, '.env');

		if (existsSync(candidate)) return candidate;

		const parent = dirname(current);
		if (parent === current) return undefined;
		current = parent;
	}
}

function loadDotenv() {
	if (envLoaded) return;

	const path = findDotenv();
	if (path) config({ path });
	envLoaded = true;
}

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
