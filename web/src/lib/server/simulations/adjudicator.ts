import { getAnthropicClient, getAnthropicConfig } from '$lib/server/anthropic/client';
import { loadSessionMessages } from '$lib/server/storage/chat';
import { procurementOperators } from '$lib/simulations/operators';
import { zodOutputFormat } from '@anthropic-ai/sdk/helpers/zod';
import { z } from 'zod';

const adjudicationSchema = z.object({
	requirements: z.array(
		z.object({
			id: z.string(),
			satisfied: z.boolean(),
			evidence: z.string().max(240)
		})
	),
	establishedFacts: z.array(z.string().max(240)).max(12),
	nextConcern: z.string().max(240).nullable()
});

export async function nextSimulationTurn(operatorId: string, sessionId: string) {
	const operator = procurementOperators.find((item) => item.id === operatorId);
	if (!operator || !sessionId) throw new Error('Simulation operator and session are required.');

	const messages = await loadSessionMessages(sessionId);
	if (!messages.length) {
		return {
			done: false,
			message: operator.openingMessage
		};
	}

	const conversation = messages.slice().reverse();
	const transcript = conversation
		.map((message) => `${message.role}: ${message.content.slice(0, 1600)}`)
		.join('\n\n');
	const recentConversation = conversation
		.slice(-10)
		.map((message) => `${message.role}: ${message.content.slice(0, 1600)}`)
		.join('\n\n');

	const { model } = getAnthropicConfig();
	const anthropic = getAnthropicClient();
	const adjudicationResponse = await anthropic.messages.parse({
		model,
		max_tokens: 3000,
		output_config: { format: zodOutputFormat(adjudicationSchema) },
		system:
			'Privately evaluate a procurement conversation against its requirements. Mark a requirement satisfied only when the transcript contains concrete support for its done condition. Return every requirement exactly once. Keep each evidence statement and established fact under 20 words. Extract only facts established by the assistant responses. If anything remains unsatisfied, choose one next business concern that advances the objective without retrying an exhausted line of inquiry; otherwise return null.',
		messages: [
			{
				role: 'user',
				content: JSON.stringify({
					requirements: operator.requirements,
					transcript
				})
			}
		]
	});

	const adjudication = adjudicationResponse.parsed_output;
	if (!adjudication) {
		throw new Error(
			`Simulation adjudicator returned no result (${adjudicationResponse.stop_reason}).`
		);
	}

	const status = new Map(
		adjudication.requirements.map((requirement) => [requirement.id, requirement.satisfied])
	);
	const done = operator.requirements.every((requirement) => status.get(requirement.id) === true);
	if (done) return { done: true, message: '' };

	const operatorResponse = await anthropic.messages.create({
		model,
		max_tokens: 1200,
		system:
			'You are the procurement operator speaking to the assistant. Respond only to the conversation in front of you. You know your business objective, but you are not completing or auditing a checklist. Make one natural conversational move in first person, using the current concern as direction rather than wording. Follow what is most salient, uncertain, or consequential in the latest answer. Ask about one connected concern at a time, accept explicitly exhausted unknowns, do not bundle unrelated requests to finish faster, and do not mention requirements, scoring, simulation, or evaluation. Return only the next message in 1-3 sentences.',
		messages: [
			{
				role: 'user',
				content: JSON.stringify({
					operator: {
						name: operator.name,
						company: operator.company,
						profile: operator.profile,
						intent: operator.intent,
						overallObjective: operator.openingMessage
					},
					currentConcern: adjudication.nextConcern,
					establishedFacts: adjudication.establishedFacts,
					recentConversation
				})
			}
		]
	});

	const message = operatorResponse.content
		.map((block) => ('text' in block ? block.text : ''))
		.join('')
		.trim();

	if (!message) throw new Error('Simulation operator returned no next message.');

	return {
		done: false,
		message
	};
}
