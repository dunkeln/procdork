<script lang="ts" module>
	export type SessionSummary = {
		slug: string;
		title: string;
		updatedAt: string;
		messageCount: number;
	};
</script>

<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Plus, Search, Trash2 } from '@lucide/svelte';
	import { tick } from 'svelte';

	let {
		sessions,
		currentSlug,
		creating = false,
		deletingSlug = '',
		onNewSession,
		onOpenSession,
		onDeleteSession,
		onRenameSession
	}: {
		sessions: SessionSummary[];
		currentSlug: string;
		creating?: boolean;
		deletingSlug?: string;
		onNewSession: () => void;
		onOpenSession: (slug: string) => void;
		onDeleteSession: (slug: string) => void;
		onRenameSession: (slug: string, title: string) => void;
	} = $props();

	let query = $state('');
	let editingSlug = $state('');
	let editingTitle = $state('');
	let titleInput = $state<HTMLInputElement>();
	let clickTimer: ReturnType<typeof setTimeout> | undefined;
	let filteredSessions = $derived(
		sessions.filter((session) => session.title.toLowerCase().includes(query.trim().toLowerCase()))
	);

	function updatedLabel(value: string) {
		const date = new Date(value);
		if (Number.isNaN(date.valueOf())) return '';

		return new Intl.DateTimeFormat(undefined, {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		}).format(date);
	}

	async function startRename(session: SessionSummary) {
		if (clickTimer) clearTimeout(clickTimer);
		editingSlug = session.slug;
		editingTitle = session.title;
		await tick();
		titleInput?.focus();
		titleInput?.select();
	}

	function saveRename() {
		if (!editingSlug) return;

		onRenameSession(editingSlug, editingTitle);
		editingSlug = '';
		editingTitle = '';
	}

	function cancelRename() {
		editingSlug = '';
		editingTitle = '';
	}

	function openAfterClick(slug: string, event: MouseEvent) {
		if (clickTimer) clearTimeout(clickTimer);
		if (event.detail > 1 || editingSlug) return;

		clickTimer = setTimeout(() => onOpenSession(slug), 260);
	}
</script>

<section class="flex min-h-0 w-full flex-1 flex-col">
	<div class="flex items-stretch gap-3">
		<div
			class="relative min-w-0 flex-1 border border-[#10120f] bg-white shadow-[6px_6px_0_#10120f]"
		>
			<Search class="absolute top-1/2 left-4 size-4 -translate-y-1/2 text-[#596154]" />
			<input
				class="h-12 w-full border-0 bg-transparent pr-4 pl-11 font-mono text-sm text-[#10120f] outline-none"
				placeholder="Search sessions..."
				bind:value={query}
			/>
		</div>
		<Button
			type="button"
			disabled={creating}
			class="h-12 shrink-0 border border-[#10120f] bg-[#10120f] text-white shadow-[4px_4px_0_#aeb7aa] hover:bg-[#10120f]/90"
			onclick={onNewSession}
		>
			<Plus />
			New chat
		</Button>
	</div>

	<div class="mt-6 min-h-0 flex-1 overflow-y-auto border-t border-[#dfe5dc] pt-4">
		{#if filteredSessions.length}
			<div class="space-y-2">
				{#each filteredSessions as session (session.slug)}
					<div
						class={[
							'group flex w-full items-center gap-3 border transition',
							session.slug === currentSlug
								? 'border-[#10120f] bg-[#10120f] text-white shadow-[3px_3px_0_#aeb7aa]'
								: 'border-[#10120f]/10 bg-white/45 text-[#10120f] hover:border-[#10120f]/30 hover:bg-white'
						]}
					>
						<button
							type="button"
							class="min-w-0 flex-1 px-3 py-3 text-left"
							onclick={(event) => openAfterClick(session.slug, event)}
							ondblclick={(event) => {
								event.preventDefault();
								startRename(session);
							}}
						>
							{#if editingSlug === session.slug}
								<input
									class={[
										'block h-5 w-full appearance-none border-0 bg-transparent p-0 text-sm font-semibold outline-none focus:border-transparent focus:ring-0',
										session.slug === currentSlug ? 'text-white' : 'text-[#10120f]'
									]}
									aria-label="Rename chat"
									bind:this={titleInput}
									bind:value={editingTitle}
									onblur={saveRename}
									onclick={(event) => event.stopPropagation()}
									onkeydown={(event) => {
										if (event.key === 'Enter') {
											event.preventDefault();
											saveRename();
										}
										if (event.key === 'Escape') {
											event.preventDefault();
											cancelRename();
										}
									}}
								/>
							{:else}
								<span class="block truncate text-sm font-semibold">{session.title}</span>
							{/if}
							<span
								class={[
									'mt-1 block font-mono text-xs',
									session.slug === currentSlug ? 'text-white/65' : 'text-[#596154]/70'
								]}
							>
								{updatedLabel(session.updatedAt)}
							</span>
						</button>
						<Button
							type="button"
							variant="ghost"
							size="sm"
							disabled={deletingSlug === session.slug}
							aria-label={`Delete ${session.title}`}
							class={[
								'mr-2 size-9 shrink-0 px-0',
								session.slug === currentSlug
									? 'text-white/75 hover:bg-white/10 hover:text-white'
									: 'text-[#596154]/75 hover:bg-[#10120f]/5 hover:text-[#10120f]'
							]}
							onclick={() => onDeleteSession(session.slug)}
						>
							<Trash2 />
						</Button>
					</div>
				{/each}
			</div>
		{:else}
			<p class="py-8 font-mono text-sm text-[#596154]/75">No sessions found.</p>
		{/if}
	</div>
</section>
