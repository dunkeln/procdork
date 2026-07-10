import architectureMarkdown from '$lib/content/architecture.md?raw';
import MarkdownIt from 'markdown-it';

const markdown = new MarkdownIt({
	html: false,
	linkify: true,
	typographer: true
});

export function load() {
	return {
		architectureHtml: markdown.render(architectureMarkdown)
	};
}
