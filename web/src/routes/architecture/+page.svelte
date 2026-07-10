<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>harness architecture</title>
	<meta
		name="description"
		content="A crawlable, paper-style architecture brief for the procdork supplier procurement workflow."
	/>
</svelte:head>

<div class="architecture-shell">
	<article class="paper" aria-labelledby="architecture-title">
		<div class="markdown-body">
			{@html data.architectureHtml}
		</div>
	</article>
</div>

<style>
	.architecture-shell {
		min-height: 100dvh;
		background: #eef0f3;
		padding: 32px 16px;
		color: #141414;
		font-family: var(--font-sans);
	}

	.paper {
		box-sizing: border-box;
		width: min(100%, 8.5in);
		min-height: 11in;
		margin: 0 auto;
		background: #fffdf8;
		border: 1px solid #ded8cc;
		box-shadow: 0 18px 48px rgb(20 20 20 / 14%);
		padding: clamp(32px, 6vw, 72px);
	}

	.markdown-body :global(h1),
	.markdown-body :global(h2),
	.markdown-body :global(h3),
	.markdown-body :global(p) {
		margin-top: 0;
	}

	.markdown-body :global(h1) {
		border-bottom: 2px solid #171717;
		margin-bottom: 14px;
		padding-bottom: 24px;
		font-size: clamp(2.75rem, 8vw, 5.75rem);
		font-weight: 700;
		line-height: 0.95;
	}

	.markdown-body :global(h2) {
		margin-top: 30px;
		margin-bottom: 12px;
		font-size: 1.05rem;
		font-weight: 600;
	}

	.markdown-body :global(h3) {
		margin-bottom: 8px;
		font-size: 0.88rem;
		font-weight: 600;
	}

	.markdown-body :global(p),
	.markdown-body :global(li) {
		color: #363636;
		font-size: 1rem;
		line-height: 1.6;
	}

	.markdown-body :global(h1 + h2) {
		margin-top: 32px;
	}

	.markdown-body :global(ol),
	.markdown-body :global(ul) {
		margin: 0;
		padding-left: 1.15rem;
	}

	.markdown-body :global(li + li) {
		margin-top: 8px;
	}

	.markdown-body :global(code) {
		background: #f2eee5;
		border: 1px solid #e3dccf;
		font-size: 0.88em;
		padding: 0.08rem 0.24rem;
	}

	@media (max-width: 720px) {
		.architecture-shell {
			padding: 16px 10px;
		}

		.paper {
			min-height: auto;
			padding: 28px 22px;
		}
	}

	@media print {
		.architecture-shell {
			background: white;
			padding: 0;
		}

		.paper {
			width: 8.5in;
			min-height: 11in;
			border: 0;
			box-shadow: none;
			margin: 0;
		}
	}
</style>
