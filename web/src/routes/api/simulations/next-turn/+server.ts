import { nextSimulationTurn } from '$lib/server/simulations/adjudicator';
import { json, type RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => null);
	const operatorId = typeof body?.operatorId === 'string' ? body.operatorId : '';
	const sessionId = typeof body?.sessionId === 'string' ? body.sessionId : '';

	try {
		return json(await nextSimulationTurn(operatorId, sessionId));
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Simulation adjudication failed.';
		const status = message.includes('configured') ? 503 : message.includes('required') ? 400 : 502;
		return json({ error: message }, { status });
	}
};
