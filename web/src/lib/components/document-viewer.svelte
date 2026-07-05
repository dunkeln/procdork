<script lang="ts">
	import { resolve } from '$app/paths';
	import { Button } from '$lib/components/ui/button';
	import { Download, ExternalLink, FileArchive, FileText } from '@lucide/svelte';

	type Props = {
		src: string;
		mimeType: string;
		title: string;
		filename?: string;
	};

	let { src, mimeType, title, filename = title }: Props = $props();

	let text = $state('');
	let textError = $state('');
	let loadingText = $state(false);
	const resolvePath = resolve as unknown as (path: string) => string;

	const textTypes = new Set([
		'application/json',
		'application/xml',
		'application/xhtml+xml',
		'text/csv',
		'text/markdown'
	]);

	const officeTypes = new Set([
		'application/msword',
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
		'application/vnd.ms-excel',
		'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		'application/vnd.ms-powerpoint',
		'application/vnd.openxmlformats-officedocument.presentationml.presentation'
	]);

	let isPdf = $derived(mimeType === 'application/pdf');
	let isImage = $derived(mimeType.startsWith('image/'));
	let isText = $derived(mimeType.startsWith('text/') || textTypes.has(mimeType));
	let isOffice = $derived(officeTypes.has(mimeType));
	let resolvedSrc = $derived(resolvePath(src));
	let pdfSrc = $derived(`${resolvedSrc}#navpanes=0&view=FitH`);

	$effect(() => {
		if (!isText) {
			text = '';
			textError = '';
			return;
		}

		const controller = new AbortController();
		loadingText = true;
		textError = '';

		fetch(resolvedSrc, { signal: controller.signal })
			.then((response) => {
				if (!response.ok) throw new Error(`Unable to load ${response.status}`);
				return response.text();
			})
			.then((content) => {
				text = content;
			})
			.catch((error: unknown) => {
				if (!controller.signal.aborted) {
					textError = error instanceof Error ? error.message : 'Unable to load document.';
				}
			})
			.finally(() => {
				if (!controller.signal.aborted) loadingText = false;
			});

		return () => controller.abort();
	});
</script>

<section class="overflow-hidden border border-[#10120f] bg-white shadow-[6px_6px_0_#10120f]">
	<div class="h-[min(68vh,760px)] min-h-96 bg-[#f8faf6]">
		{#if isPdf}
			<iframe class="h-full w-full border-0 bg-white" src={pdfSrc} {title}></iframe>
		{:else if isImage}
			<div class="grid h-full place-items-center overflow-auto p-4">
				<img class="max-h-full max-w-full object-contain" src={resolvedSrc} alt={title} />
			</div>
		{:else if isText}
			<pre
				class="h-full overflow-auto whitespace-pre-wrap p-4 font-mono text-sm leading-6 text-[#10120f]">{loadingText
					? 'Loading document...'
					: textError || text}</pre>
		{:else}
			<div class="grid h-full place-items-center p-6 text-center">
				<div class="max-w-sm">
					{#if isOffice}
						<FileArchive class="mx-auto mb-4 size-8 text-[#2d6d4d]" />
						<h3 class="text-lg font-semibold">Office document preview is not native.</h3>
					{:else}
						<FileText class="mx-auto mb-4 size-8 text-[#2d6d4d]" />
						<h3 class="text-lg font-semibold">Preview unavailable for this MIME type.</h3>
					{/if}
					<p class="mt-2 text-sm leading-6 text-[#596154]">
						This viewer hosts the file and falls back to open or download when the browser cannot
						render the MIME type directly.
					</p>
					<div class="mt-4 flex justify-center gap-2">
						<Button
							class="h-8 border-[#cfd8ca] bg-white px-2.5 text-xs hover:bg-[#eef3ea]"
							variant="outline"
							size="sm"
							href={resolvedSrc}
							target="_blank"
						>
							<ExternalLink class="size-3.5" />
							Open
						</Button>
						<Button
							class="h-8 bg-[#10120f] px-2.5 text-xs text-white hover:bg-[#10120f]/90"
							size="sm"
							href={resolvedSrc}
							download={filename}
						>
							<Download class="size-3.5" />
							Download
						</Button>
					</div>
				</div>
			</div>
		{/if}
	</div>
</section>
