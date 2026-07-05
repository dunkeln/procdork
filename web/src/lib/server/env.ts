import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { config } from 'dotenv';

let loaded = false;

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

export function loadDotenv() {
	if (loaded) return;

	const path = findDotenv();
	if (path) config({ path });
	loaded = true;
}
