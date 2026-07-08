type NextTurn = {
	done: boolean;
	message: string;
};

export async function runOperatorSimulation(input: {
	operatorId: string;
	sessionId: string;
	nextTurn: (operatorId: string, sessionId: string) => Promise<NextTurn>;
	submitTurn: (message: string, sessionId: string) => Promise<boolean>;
}) {
	while (true) {
		const next = await input.nextTurn(input.operatorId, input.sessionId);
		if (next.done) return true;
		if (!next.message) throw new Error('Simulation produced no next operator message.');

		const ok = await input.submitTurn(next.message, input.sessionId);
		if (!ok) return false;
	}
}
