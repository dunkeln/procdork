import { getAnthropicClient, getAnthropicConfig } from '$lib/server/anthropic/client';
import { loadSessionMessages } from '$lib/server/storage/chat';
import { procurementOperators } from '$lib/simulations/operators';

function parseJsonObject(text: string) {
	const start = text.indexOf('{');
	const end = text.lastIndexOf('}');
	if (start === -1 || end === -1 || end <= start) return null;

	return JSON.parse(text.slice(start, end + 1)) as unknown;
}

export async function nextSimulationTurn(operatorId: string, sessionId: string) {
	const operator = procurementOperators.find((item) => item.id === operatorId);
	if (!operator || !sessionId) throw new Error('Simulation operator and session are required.');

	const messages = await loadSessionMessages(sessionId);
	if (!messages.length) {
		return {
			done: false,
			message: operator.openingMessage,
			satisfied: [],
			missing: operator.requirements.map((item) => item.id),
			requirements: operator.requirements
		};
	}

	const transcript = messages
		.slice()
		.reverse()
		.slice(-12)
		.map((message) => `${message.role}: ${message.content.slice(0, 1600)}`)
		.join('\n\n');

	const { model } = getAnthropicConfig();
	const response = await getAnthropicClient().messages.create({
		model,
		max_tokens: 700,
		system:
			'You simulate a real procurement operator, not the assistant. Decide whether the procurement requirement is satisfied from the transcript. If gaps remain, ask the next natural first-person follow-up as the operator. Do not roleplay the assistant. Return only compact JSON.',
		messages: [
			{
				role: 'user',
				content: JSON.stringify({
					operator: {
						name: operator.name,
						company: operator.company,
						profile: operator.profile,
						intent: operator.intent
					},
					requirements: operator.requirements,
					transcript,
					response_shape: {
						done: 'boolean',
						satisfied: ['requirement-id'],
						missing: ['requirement-id'],
						message: 'next operator message, empty when done'
					}
				})
			}
		]
	});

	const text = response.content
		.map((block) => ('text' in block ? block.text : ''))
		.join('')
		.trim();
	const parsed = parseJsonObject(text);

	if (
		typeof parsed !== 'object' ||
		parsed === null ||
		!('done' in parsed) ||
		typeof parsed.done !== 'boolean'
	) {
		throw new Error('Simulation adjudicator returned invalid JSON.');
	}

	return {
		done: parsed.done,
		message: 'message' in parsed && typeof parsed.message === 'string' ? parsed.message.trim() : '',
		satisfied: 'satisfied' in parsed && Array.isArray(parsed.satisfied) ? parsed.satisfied : [],
		missing: 'missing' in parsed && Array.isArray(parsed.missing) ? parsed.missing : [],
		requirements: operator.requirements
	};
}
