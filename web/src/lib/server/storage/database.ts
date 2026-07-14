import { loadDotenv } from '$lib/server/env';
import { neon } from '@neondatabase/serverless';
import schemaSql from './schema.sql?raw';

type Db = ReturnType<typeof neon>;

let db: Db | undefined;
let init: Promise<void> | undefined;

export function database() {
	loadDotenv();
	const databaseUrl = process.env.DATABASE_URL;
	if (!databaseUrl) throw new Error('DATABASE_URL is not configured.');

	db ??= neon(databaseUrl);
	return db;
}

export async function ensureStorageSchema() {
	init ??= (async () => {
		for (const statement of schemaSql
			.split(/;\s*\n/)
			.map((item) => item.trim())
			.filter(Boolean)) {
			await database().query(statement);
		}
	})();
	return init;
}
