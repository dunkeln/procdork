import { json, type RequestHandler } from '@sveltejs/kit';
import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const whiteboardPath = join(process.cwd(), 'static', 'assets', 'procdork-architecture.excalidraw');

export const GET: RequestHandler = async () => {
	const content = await readFile(whiteboardPath, 'utf8');
	return new Response(content, {
		headers: {
			'content-type': 'application/json'
		}
	});
};

export const PUT: RequestHandler = async ({ request }) => {
	const payload = await request.json();

	if (payload?.type !== 'excalidraw' || !Array.isArray(payload?.elements)) {
		return json({ ok: false, error: 'Expected an Excalidraw scene.' }, { status: 400 });
	}

	await writeFile(whiteboardPath, `${JSON.stringify(payload, null, 2)}\n`);
	return json({ ok: true });
};
