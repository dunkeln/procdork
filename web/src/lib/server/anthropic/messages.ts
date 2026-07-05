import type { RawMessageStreamEvent } from '@anthropic-ai/sdk/resources/messages';

export function streamText(event: RawMessageStreamEvent) {
	return event.type === 'content_block_delta' &&
		event.delta.type === 'text_delta' &&
		typeof event.delta.text === 'string'
		? event.delta.text
		: '';
}

export function textFrom(content: unknown[]) {
	return content
		.map((block) =>
			typeof block === 'object' &&
			block !== null &&
			'type' in block &&
			block.type === 'text' &&
			'text' in block &&
			typeof block.text === 'string'
				? block.text
				: ''
		)
		.join('');
}
