import { loadDotenv } from '$lib/server/env';
import Anthropic from '@anthropic-ai/sdk';

let client: Anthropic | undefined;

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
