<script lang="ts" module>
	export type EmailDraftValue = {
		subject: string;
		body: string;
	};
</script>

<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Check, Copy, Mail } from '@lucide/svelte';

	let { draft }: { draft: EmailDraftValue } = $props();
	let copied = $state(false);
	let mailtoHref = $derived(
		`mailto:?subject=${encodeURIComponent(draft.subject)}&body=${encodeURIComponent(draft.body)}`
	);

	async function copyDraft() {
		await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`);
		copied = true;
		setTimeout(() => (copied = false), 1200);
	}
</script>

<section class="mt-3 border border-[#10120f] bg-white text-sm shadow-[3px_3px_0_#aeb7aa]">
	<div class="flex items-center justify-between gap-2 border-b border-[#dfe5dc] px-3 py-2 font-mono text-xs text-[#596154]">
		{draft.subject}
		<div class="flex items-center gap-1">
			<Button
				type="button"
				variant="ghost"
				size="icon-xs"
				aria-label="Copy email draft"
				onclick={copyDraft}
			>
				{#if copied}
					<Check />
				{:else}
					<Copy />
				{/if}
			</Button>
			<Button href={mailtoHref} variant="ghost" size="sm" class="font-mono text-xs">
				<Mail />
				open draft
			</Button>
		</div>
	</div>
	<pre class="whitespace-pre-wrap px-3 py-3 font-sans leading-6 text-[#10120f]">{draft.body}</pre>
</section>
