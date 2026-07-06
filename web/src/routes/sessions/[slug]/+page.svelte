<script lang="ts">
	import { resolve } from '$app/paths';
	import { goto, invalidateAll } from '$app/navigation';
	import { page } from '$app/state';
	import ChatBox, { type ChatMessage, type EvidenceItem } from '$lib/components/chat-box.svelte';
	import SessionsList from '$lib/components/sessions-list.svelte';
	import logo from '$lib/assets/procdork-logo.png';
	import { Button } from '$lib/components/ui/button';
	import { ChevronRight, Search, SendHorizontal, X } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import { tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	let query = $state('');
	let loading = $state(false);
	let error = $state('');
	let creatingSession = $state(false);
	let deletingSession = $state('');
	let workspaceMode = $state<'chat' | 'sessions'>('chat');
	let liveMessages = $state<ChatMessage[] | null>(null);
	let messages = $derived((liveMessages ?? data.messages) as ChatMessage[]);
	let hasSearched = $derived(data.messages.length > 0 || liveMessages !== null);
	let hasQuery = $derived(Boolean(query.trim()));
	let isCompact = $derived(hasQuery || hasSearched || messages.length > 0);
	let currentSlug = $derived(page.params.slug ?? '');
	let queryBox = $state<HTMLTextAreaElement>();
	let toolFailureToastKeys = $state<string[]>([]);

	onMount(() => {
		if (data.persistenceWarning) {
			toast.warning('Persistence unavailable', {
				description: data.persistenceWarning
			});
		}
	});

	async function newSession() {
		if (creatingSession) return;

		creatingSession = true;
		try {
			const response = await fetch('/api/sessions', { method: 'POST' });
			const data = await response.json().catch(() => null);

			if (!response.ok || typeof data?.slug !== 'string') {
				throw new Error(data?.error ?? 'Session creation failed.');
			}

			await goto(resolve(`/sessions/${data.slug}`));
		} catch (caught) {
			toast.error('Session creation failed', {
				description: caught instanceof Error ? caught.message : 'Could not create a Neon session.'
			});
		} finally {
			creatingSession = false;
		}
	}

	function openSession(slug: string) {
		workspaceMode = 'chat';
		goto(resolve(`/sessions/${slug}`));
	}

	async function deleteSession(slug: string) {
		if (deletingSession) return;

		deletingSession = slug;
		try {
			const response = await fetch(resolve(`/api/sessions/${slug}`), { method: 'DELETE' });
			const data = await response.json().catch(() => null);

			if (!response.ok) {
				throw new Error(data?.error ?? 'Session deletion failed.');
			}

			toast.success('Session deleted');

			if (slug === currentSlug) {
				await goto(resolve('/'));
			} else {
				await invalidateAll();
			}
		} catch (caught) {
			toast.error('Session deletion failed', {
				description: caught instanceof Error ? caught.message : 'Could not delete the session.'
			});
		} finally {
			deletingSession = '';
		}
	}

	async function renameSession(slug: string, title: string) {
		try {
			const response = await fetch(resolve(`/api/sessions/${slug}`), {
				method: 'PATCH',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ title })
			});
			const data = await response.json().catch(() => null);

			if (!response.ok) {
				throw new Error(data?.error ?? 'Session rename failed.');
			}

			await invalidateAll();
		} catch (caught) {
			toast.error('Session rename failed', {
				description: caught instanceof Error ? caught.message : 'Could not rename the session.'
			});
		}
	}

	function resizeQueryBox() {
		if (!queryBox) return;

		queryBox.style.height = 'auto';
		queryBox.style.height = `${Math.min(queryBox.scrollHeight, 104)}px`;
		queryBox.style.overflowY = queryBox.scrollHeight > 104 ? 'auto' : 'hidden';
	}

	function updateMessage(id: string, patch: Partial<ChatMessage>) {
		liveMessages = messages.map((message) =>
			message.id === id ? { ...message, ...patch } : message
		);
	}

	function appendToMessage(id: string, text: string) {
		liveMessages = messages.map((message) =>
			message.id === id ? { ...message, content: message.content + text } : message
		);
	}

	function appendProgress(id: string, text: string) {
		liveMessages = messages.map((message) =>
			message.id === id ? { ...message, progress: `${message.progress ?? ''}${text}` } : message
		);
	}

	function handleStreamEvent(event: unknown, assistantId: string) {
		if (typeof event !== 'object' || event === null || !('type' in event)) return;

		if (event.type === 'delta' && 'text' in event && typeof event.text === 'string') {
			if ('channel' in event && event.channel === 'progress') {
				appendProgress(assistantId, event.text);
			} else {
				appendToMessage(assistantId, event.text);
			}
		}

		if (event.type === 'evidence' && 'evidence' in event && Array.isArray(event.evidence)) {
			updateMessage(assistantId, { evidence: event.evidence as EvidenceItem[] });
		}

		if (
			event.type === 'final' &&
			'citations' in event &&
			'suggestEmail' in event &&
			Array.isArray(event.citations)
		) {
			updateMessage(assistantId, {
				...('prose' in event && typeof event.prose === 'string' ? { content: event.prose } : {}),
				evidence: event.citations as EvidenceItem[],
				suggestEmail: event.suggestEmail === true,
				suggestEmailLabel:
					'suggestEmailLabel' in event && typeof event.suggestEmailLabel === 'string'
						? event.suggestEmailLabel
						: undefined
			});
		}

		if (
			event.type === 'tool' &&
			'label' in event &&
			'status' in event &&
			typeof event.label === 'string' &&
			(event.status === 'running' || event.status === 'done' || event.status === 'error')
		) {
			updateMessage(assistantId, { tool: { label: event.label, status: event.status } });

			if (event.status === 'error') {
				const key = `${assistantId}:${event.label}`;

				if (!toolFailureToastKeys.includes(key)) {
					toolFailureToastKeys = [...toolFailureToastKeys, key];
					toast.warning(`${event.label} failed`, {
						description: 'Continuing with the evidence available.'
					});
				}
			}
		}

		if (event.type === 'error' && 'error' in event && typeof event.error === 'string') {
			error = event.error;
			updateMessage(assistantId, { loading: false });
			toast.error('Runtime failed', {
				description: event.error
			});
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
		const sessionId = currentSlug ?? 'ephemeral';

		loading = true;
		error = '';
		toolFailureToastKeys = [];
		liveMessages = [
			{ id: userId, role: 'user', content: message },
			{
				id: assistantId,
				role: 'assistant',
				content: '',
				originalRequest: message,
				loading: true,
				evidence: []
			},
			...messages
		];
		query = '';
		await tick();
		resizeQueryBox();

		try {
			const response = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ message, sessionId })
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

	async function draftEmail(message: ChatMessage) {
		if (message.emailLoading || message.emailDraft) return;

		updateMessage(message.id, { emailLoading: true });

		try {
			const response = await fetch('/api/chat/email', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({
					message: message.originalRequest ?? message.content,
					prose: message.content,
					citations: message.evidence ?? []
				})
			});
			const data = await response.json().catch(() => null);

			if (!response.ok) throw new Error(data?.error ?? 'Email draft failed.');

			updateMessage(message.id, {
				emailDraft: {
					subject: data.subject ?? 'Supplier quote request',
					body: data.body ?? ''
				},
				emailLoading: false
			});
		} catch (caught) {
			updateMessage(message.id, { emailLoading: false });
			toast.error('Email draft failed', {
				description:
					caught instanceof Error ? caught.message : 'The runtime did not return a draft.'
			});
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
			<Button
				type="button"
				variant="outline"
				size="sm"
				class="border-[#10120f]/20 bg-white/70"
				onclick={() => (workspaceMode = workspaceMode === 'sessions' ? 'chat' : 'sessions')}
			>
				{#if workspaceMode === 'sessions'}
					<X />
					Back to chat
				{:else}
					<Search />
					Search sessions
				{/if}
			</Button>
		</header>

		<div class="flex min-h-0 flex-1 overflow-hidden py-8 lg:py-10">
			<section id="search" class="flex min-h-0 w-full min-w-0 overflow-hidden">
				<div class="flex min-h-0 w-full overflow-hidden">
					<div
						class="mx-auto flex min-h-0 w-full flex-1 flex-col overflow-hidden transition-all duration-300 lg:w-[70%] lg:flex-none"
					>
						{#if workspaceMode === 'sessions'}
							<SessionsList
								sessions={data.sessions}
								{currentSlug}
								creating={creatingSession}
								deletingSlug={deletingSession}
								onNewSession={newSession}
								onOpenSession={openSession}
								onDeleteSession={deleteSession}
								onRenameSession={renameSession}
							/>
						{:else}
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
									isCompact
										? 'mt-0 max-h-0 translate-y-[-8px] opacity-0'
										: 'mt-5 max-h-24 opacity-100'
								]}
							>
								Search filings, vendor pages, news, and research through a web search agent.
							</p>
							<form
								class={[
									'relative w-full shrink-0 border border-[#10120f] bg-white shadow-[6px_6px_0_#10120f] transition-all duration-300',
									isCompact ? 'mt-0' : 'mt-8'
								]}
								onsubmit={(event) => (event.preventDefault(), runSearch())}
							>
								<textarea
									bind:this={queryBox}
									class="block max-h-[104px] min-h-12 w-full resize-none border-0 bg-transparent py-3 pr-24 pl-4 font-mono text-sm leading-5 text-[#10120f] outline-none focus:ring-0"
									maxlength="500"
									placeholder="Search and query suppliers..."
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
								<ChatBox {messages} onDraftEmail={draftEmail} />
							{/if}
						{/if}
					</div>
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
