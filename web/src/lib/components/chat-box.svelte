<script lang="ts" module>
	export type EvidenceItem = {
		title: string;
		url: string;
		snippet?: string;
		source: 'search' | 'fetch' | 'document';
	};

	export type ChatMessage = {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		originalRequest?: string;
		loading?: boolean;
		evidence?: EvidenceItem[];
		suggestEmail?: boolean;
		suggestEmailLabel?: string;
		emailLoading?: boolean;
		emailDraft?: {
			subject: string;
			body: string;
		};
		tool?: {
			label: string;
			status: 'running' | 'done' | 'error';
		};
	};
</script>

<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import EmailDraft from '$lib/components/email-draft.svelte';
	import { LoaderCircle, Mail } from '@lucide/svelte';
	import MarkdownIt from 'markdown-it';

	let {
		messages,
		onDraftEmail
	}: { messages: ChatMessage[]; onDraftEmail: (message: ChatMessage) => void } = $props();

	const markdown = new MarkdownIt({
		html: false,
		linkify: true,
		breaks: true
	});

	function renderMarkdown(content: string) {
		return markdown.render(content || '');
	}
</script>

<section
	class="mt-5 min-h-0 w-full max-w-2xl flex-1 overflow-y-auto border-t border-[#dfe5dc] pt-5"
	aria-label="Chat history"
>
	<div class="space-y-4">
		{#each messages as message (message.id)}
			<article
				class={[
					'flex w-full',
					message.role === 'user' ? 'justify-end pl-12' : 'justify-start pr-12'
				]}
			>
				{#if message.role === 'user'}
					<p
						class="max-w-[84%] border border-[#10120f] bg-[#10120f] px-3 py-2 font-mono text-sm leading-6 whitespace-pre-wrap text-white shadow-[3px_3px_0_#aeb7aa]"
					>
						{message.content}
					</p>
				{:else}
					<div class="max-w-[88%]">
						{#if message.tool}
							<Badge
								variant="ghost"
								class="mb-2 bg-[#eef3ec] font-mono text-[11px] text-[#596154]"
							>
								{#if message.tool.status === 'running'}
									<LoaderCircle class="animate-spin" />
								{/if}
								{message.tool.label}
							</Badge>
						{/if}
						<div
							class="prose prose-sm max-w-none prose-headings:mt-0 prose-headings:text-[#10120f] prose-p:leading-6 prose-a:text-[#10120f] prose-strong:text-[#10120f] text-[#10120f]"
						>
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							{@html renderMarkdown(message.content || (message.loading ? 'Thinking...' : ''))}
						</div>
						{#if message.evidence?.length}
							<div class="mt-2 flex flex-wrap gap-2">
								{#each message.evidence as item (item.url)}
									<a
										href={item.url}
										class="text-xs text-[#5d675b] underline decoration-[#aeb7aa] underline-offset-4 hover:text-[#10120f]"
										target="_blank"
										rel="noreferrer"
									>
										{item.title}
									</a>
								{/each}
							</div>
						{/if}
						{#if message.suggestEmail && !message.emailDraft}
							<Button
								type="button"
								variant="outline"
								size="sm"
								disabled={message.emailLoading}
								class="mt-3 border-[#10120f] bg-[#10120f] text-xs text-white hover:bg-[#10120f]/90"
								onclick={() => onDraftEmail(message)}
							>
								{#if message.emailLoading}
									<LoaderCircle class="animate-spin" />
								{:else}
									<Mail />
								{/if}
								{message.suggestEmailLabel ?? 'Suggest email'}
							</Button>
						{/if}
						{#if message.emailDraft}
							<EmailDraft draft={message.emailDraft} />
						{/if}
					</div>
				{/if}
			</article>
		{/each}
	</div>
</section>
