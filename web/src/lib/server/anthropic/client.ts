import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import Anthropic from '@anthropic-ai/sdk';
import { config } from 'dotenv';

let client: Anthropic | undefined;
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

export function getAnthropicConfig() {
	loadDotenv();

	const apiKey = process.env.ANTHROPIC_API_KEY;
	const model = process.env.ANTHROPIC_MODEL;

	if (!apiKey || !model) {
		throw new Error('Anthropic API key or model is not configured.');
	}

	return { apiKey, model };
}

export function getAnthropicClient() {
	const { apiKey } = getAnthropicConfig();

	client ??= new Anthropic({ apiKey });
	return client;
}
