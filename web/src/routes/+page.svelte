<script lang="ts">
	import { resolve } from '$app/paths';
	import ChatBox, { type ChatMessage, type EvidenceItem } from '$lib/components/chat-box.svelte';
	import logo from '$lib/assets/procdork-logo.png';
	import { Button } from '$lib/components/ui/button';
	import { ArrowUpRight, ChevronRight, Search, SendHorizontal } from '@lucide/svelte';
	import { tick } from 'svelte';
	import { toast } from 'svelte-sonner';

	const docsUrl = 'https://docs.tinyfish.ai/search-api/reference';

	let query = $state('');
	let loading = $state(false);
	let error = $state('');
	let messages = $state<ChatMessage[]>([]);
	let hasSearched = $state(false);
	let hasQuery = $derived(Boolean(query.trim()));
	let isCompact = $derived(hasQuery || hasSearched || messages.length > 0);
	let queryBox: HTMLTextAreaElement;

	function resizeQueryBox() {
		if (!queryBox) return;

		queryBox.style.height = 'auto';
		queryBox.style.height = `${Math.min(queryBox.scrollHeight, 104)}px`;
		queryBox.style.overflowY = queryBox.scrollHeight > 104 ? 'auto' : 'hidden';
	}

	function updateMessage(id: string, patch: Partial<ChatMessage>) {
		messages = messages.map((message) => (message.id === id ? { ...message, ...patch } : message));
	}

	function appendToMessage(id: string, text: string) {
		messages = messages.map((message) =>
			message.id === id ? { ...message, content: message.content + text } : message
		);
	}

	function handleStreamEvent(event: unknown, assistantId: string) {
		if (typeof event !== 'object' || event === null || !('type' in event)) return;

		if (event.type === 'delta' && 'text' in event && typeof event.text === 'string') {
			appendToMessage(assistantId, event.text);
		}

		if (event.type === 'evidence' && 'evidence' in event && Array.isArray(event.evidence)) {
			updateMessage(assistantId, { evidence: event.evidence as EvidenceItem[] });
		}

		if (
			event.type === 'tool' &&
			'label' in event &&
			'status' in event &&
			typeof event.label === 'string' &&
			(event.status === 'running' || event.status === 'done' || event.status === 'error')
		) {
			updateMessage(assistantId, { tool: { label: event.label, status: event.status } });
		}

		if (event.type === 'error' && 'error' in event && typeof event.error === 'string') {
			error = event.error;
			updateMessage(assistantId, { loading: false });
		}

		if (event.type === 'done') {
			updateMessage(assistantId, { loading: false });
		}
	}

	async function runSearch() {
		const message = query.trim();
		if (!message || loading) return;

		const userId = crypto.randomUUID();
		const assistantId = crypto.randomUUID();

		loading = true;
		error = '';
		hasSearched = true;
		messages = [
			{ id: userId, role: 'user', content: message },
			{ id: assistantId, role: 'assistant', content: '', loading: true, evidence: [] },
			...messages
		];
		query = '';
		await tick();
		resizeQueryBox();

		try {
			const response = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ message })
			});

			if (!response.ok) {
				const data = await response.json().catch(() => null);
				error = data.error ?? 'Search failed.';
				updateMessage(assistantId, { content: error, loading: false });
				toast.error('Search failed', {
					description: error
				});
				return;
			}

			const reader = response.body?.getReader();
			if (!reader) throw new Error('Chat stream did not start.');

			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { value, done } = await reader.read();
				buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
				const lines = buffer.split('\n');
				buffer = lines.pop() ?? '';

				for (const line of lines) {
					if (line.trim()) handleStreamEvent(JSON.parse(line), assistantId);
				}

				if (done) break;
			}

			toast.success('Answer ready', {
				description: 'Response streamed into the chatbox'
			});
		} catch (caught) {
			error = caught instanceof Error ? caught.message : 'Chat failed before the runtime returned.';
			updateMessage(assistantId, { content: error, loading: false });
			toast.error('Search failed', {
				description: error
			});
		} finally {
			loading = false;
		}
	}
</script>

<section class="h-dvh overflow-hidden bg-[#f8faf6] text-[#10120f]">
	<div
		class="pointer-events-none fixed inset-0 opacity-[0.055] [background-image:radial-gradient(#10120f_0.8px,transparent_0.8px)] [background-size:16px_16px]"
	></div>

	<div class="relative mx-auto flex h-dvh w-full max-w-7xl flex-col px-4 py-4 sm:px-6 lg:px-8">
		<header
			class="flex items-center justify-between gap-4 border-b border-[#dfe5dc] bg-[#f8faf6]/90 pb-4 backdrop-blur"
		>
			<a class="flex items-center gap-2 text-sm font-semibold" href={resolve('/')}>
				<img class="size-11 object-contain" src={logo} alt="" />
				<span>procdork</span>
				<span class="font-normal text-[#596154]/70 italic">&lt;search/&gt;</span>
			</a>
			<Button href={docsUrl} variant="outline" size="sm" class="border-[#10120f]/20 bg-white/70">
				TinyFish docs
				<ArrowUpRight />
			</Button>
		</header>

		<div class="flex min-h-0 flex-1 overflow-hidden py-8 lg:py-10">
			<section id="search" class="flex min-h-0 w-full max-w-3xl min-w-0 flex-col overflow-hidden">
				<div class="flex min-h-0 w-full max-w-2xl flex-1 flex-col overflow-hidden">
					<h1
						class={[
							'overflow-hidden text-5xl leading-[0.96] font-semibold tracking-normal text-balance transition-all duration-300 md:text-7xl',
							isCompact ? 'max-h-0 translate-y-[-12px] opacity-0' : 'max-h-44 opacity-100'
						]}
					>
						Procure suppliers from the live web.
					</h1>
					<p
						class={[
							'max-w-xl overflow-hidden text-base leading-7 text-[#596154] transition-all duration-300 md:text-lg',
							isCompact ? 'mt-0 max-h-0 translate-y-[-8px] opacity-0' : 'mt-5 max-h-24 opacity-100'
						]}
					>
						Search filings, vendor pages, news, and research through a web search agent.
					</p>
					<form
						class={[
							'relative max-w-2xl shrink-0 border border-[#10120f] bg-white shadow-[6px_6px_0_#10120f] transition-all duration-300',
							isCompact ? 'mt-0' : 'mt-8'
						]}
						onsubmit={(event) => (event.preventDefault(), runSearch())}
					>
						<textarea
							bind:this={queryBox}
							class="block max-h-[104px] min-h-12 w-full resize-none border-0 bg-transparent py-3 pr-24 pl-4 font-mono text-sm leading-5 text-[#10120f] outline-none focus:ring-0"
							maxlength="500"
							placeholder="Search suppliers..."
							rows="1"
							bind:value={query}
							oninput={resizeQueryBox}
							onkeydown={(event) => {
								if (event.key === 'Enter' && !event.shiftKey) {
									event.preventDefault();
									runSearch();
								}
							}}></textarea>
						<Button
							type="submit"
							disabled={loading || !query.trim()}
							aria-label={hasSearched ? 'Send query' : 'Search'}
							class={[
								'absolute right-0 bottom-0 h-12 border-l border-[#10120f] bg-[#10120f] text-sm text-white hover:bg-[#10120f]/90',
								hasSearched ? 'w-12 px-0' : 'px-4'
							]}
						>
							{#if hasSearched}
								<SendHorizontal />
							{:else}
								<Search />
								{loading ? 'Searching' : 'Search'}
							{/if}
						</Button>
					</form>
					{#if error}
						<p class="mt-3 shrink-0 text-sm text-[#9a321d]">{error}</p>
					{/if}
					{#if messages.length}
						<ChatBox {messages} />
					{/if}
				</div>
			</section>
		</div>

		<div
			class="mt-auto flex flex-wrap items-center gap-2 border-t border-[#dfe5dc] bg-[#f8faf6]/90 py-4 text-xs text-[#596154] backdrop-blur"
		>
			<span class="font-semibold text-[#10120f]">TinyFish-inspired pattern:</span>
			<span>command</span>
			<ChevronRight class="size-3" />
			<span>server connector</span>
		</div>
	</div>
</section>
