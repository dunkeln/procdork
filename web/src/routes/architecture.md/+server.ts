import architectureMarkdown from '$lib/content/architecture.md?raw';

export function GET() {
	return new Response(architectureMarkdown, {
		headers: {
			'content-type': 'text/markdown; charset=utf-8'
		}
	});
}
