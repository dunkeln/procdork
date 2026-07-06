<script lang="ts" module>
	export type EvidenceItem = {
		title: string;
		url: string;
		snippet?: string;
		source: 'search' | 'fetch' | 'document';
		retrieved_at?: string;
		document_type?: string;
		mime_hint?: string;
	};

	export type ChatMessage = {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		progress?: string;
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

	function evidenceLabel(item: EvidenceItem, index: number) {
		const prefix = `[${index + 1}]`;
		if (item.source === 'document' && item.document_type) {
			return `${prefix} ${item.document_type} · ${item.title}`;
		}
		return `${prefix} ${item.title}`;
	}

	let chatHistory: HTMLElement;
	let currentHeadId = $state('');

	$effect(() => {
		const nextHeadId = messages[0]?.id ?? '';
		if (!chatHistory || nextHeadId === currentHeadId) return;

		currentHeadId = nextHeadId;
		chatHistory.scrollTop = 0;
	});
</script>

<section
	bind:this={chatHistory}
	class="mt-5 min-h-0 w-full flex-1 overflow-y-auto border-t border-[#dfe5dc] pt-5"
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
							<Badge variant="ghost" class="mb-2 bg-[#eef3ec] font-mono text-[11px] text-[#596154]">
								{#if message.tool.status === 'running'}
									<LoaderCircle class="animate-spin" />
								{/if}
								{message.tool.label}
							</Badge>
						{:else if message.loading && !message.content}
							<Badge variant="ghost" class="mb-2 bg-[#eef3ec] font-mono text-[11px] text-[#596154]">
								<LoaderCircle class="animate-spin" />
								working
							</Badge>
						{/if}
						{#if message.progress && !message.content}
							<div
								class="mb-3 max-w-[72ch] border-l border-[#10120f]/10 pl-3 font-mono text-xs leading-5 whitespace-pre-wrap text-[#596154]/70"
							>
								{message.progress}
							</div>
						{/if}
						<div
							class="prose prose-sm max-w-none prose-headings:mt-0 prose-headings:text-[#10120f] prose-p:leading-6 prose-a:text-[#10120f] prose-strong:text-[#10120f] text-[#10120f]"
						>
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							{@html renderMarkdown(message.content)}
						</div>
						{#if message.evidence?.length}
							<details class="group mt-3 text-xs text-[#596154]/75">
								<summary
									class="inline-flex cursor-pointer list-none items-center gap-2 border border-[#10120f]/5 bg-transparent px-2 py-1 font-mono text-[#596154]/70 transition hover:border-[#10120f]/10 hover:text-[#596154] [&::-webkit-details-marker]:hidden"
								>
									evidence · {message.evidence.length}
									<span class="text-[#596154]/45 transition group-open:rotate-90">›</span>
								</summary>
								<div class="mt-2 space-y-1 border-l border-[#10120f]/5 pl-3">
									{#each message.evidence as item, index (item.url)}
										<!-- eslint-disable svelte/no-navigation-without-resolve -->
										<a
											href={item.url}
											class="block py-0.5 text-[#596154]/70 decoration-[#aeb7aa]/50 underline-offset-4 hover:text-[#10120f] hover:underline"
											target="_blank"
											rel="noreferrer"
										>
											{evidenceLabel(item, index)}
										</a>
										<!-- eslint-enable svelte/no-navigation-without-resolve -->
									{/each}
								</div>
							</details>
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
