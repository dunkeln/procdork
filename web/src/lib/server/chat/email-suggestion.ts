import type { ChatCitation } from '$lib/server/tinyfish/procurement-tools';

export function shouldSuggestEmail(message: string) {
	return /\b(email|outreach|quote|rfq|intro|contact|supplier)\b/i.test(message);
}

function maskedEmail(text: string) {
	const email = text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0];
	if (!email) return '';

	const [user, domain] = email.split('@');
	return `${user.slice(0, Math.min(3, user.length))}...@${domain}`;
}

function supplierName(text: string) {
	const match = text.match(
		/(?:recommend(?:ed)?|best option|best supplier|choose|selected supplier)(?:\s+is|\s*:)?\s+[*_`"]*([A-Z][A-Za-z0-9&.,' -]{2,60})/i
	);
	return match?.[1]?.replace(/[*_`".,]+$/g, '').trim() ?? '';
}

export function suggestEmailLabel(message: string, finalText: string, citations: ChatCitation[]) {
	if (!shouldSuggestEmail(message)) return undefined;

	const context = [
		finalText,
		message,
		...citations.flatMap((item) => [item.title, item.snippet ?? ''])
	]
		.filter(Boolean)
		.join('\n');
	const supplier = supplierName(context);
	const email = maskedEmail(context);

	if (supplier && email) return `Write email to ${supplier} (${email})`;
	if (supplier) return `Write email to ${supplier}`;
	if (email) return `Write email (${email})`;
	return 'Write email';
}
