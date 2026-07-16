<script lang="ts">
	import DocsNav from './_components/docs-nav.svelte';

	let { children } = $props();
</script>

<section class="min-h-dvh bg-[#f8faf6] px-4 py-8 text-[#10120f] sm:px-6 lg:px-8">
	<div class="docs-shell">
		<DocsNav />
		<article class="docs-article border border-[#10120f] bg-white p-6 shadow-[6px_6px_0_#10120f] sm:p-10">
			<a class="github-link" href="https://github.com/dunkeln/procdork" target="_blank" rel="noreferrer">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path
						d="M12 1.9c-5.6 0-10.1 4.5-10.1 10.1 0 4.5 2.9 8.3 6.9 9.6.5.1.7-.2.7-.5v-1.8c-2.8.6-3.4-1.2-3.4-1.2-.5-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 0 1.6 1 1.6 1 .9 1.5 2.3 1.1 2.9.8.1-.7.4-1.1.7-1.3-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.8 1 .8-.2 1.6-.3 2.5-.3s1.7.1 2.5.3c1.9-1.3 2.8-1 2.8-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.8-4.6 5 .4.3.7.9.7 1.8v2.7c0 .3.2.6.7.5 4-1.3 6.9-5.1 6.9-9.6 0-5.6-4.5-10.1-10.1-10.1z"
					/>
				</svg>
				<span>GitHub</span>
			</a>
			{@render children()}
		</article>
	</div>
</section>

<style>
	.docs-shell {
		display: grid;
		grid-template-columns: 180px minmax(0, 56rem);
		gap: 24px;
		max-width: 72rem;
		margin: 0 auto;
	}

	article {
		position: relative;
	}

	.github-link {
		position: absolute;
		top: 40px;
		right: 40px;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		border: 1px solid #10120f;
		background: white;
		padding: 8px 10px;
		color: #10120f;
		font-size: 0.82rem;
		font-weight: 700;
		line-height: 1;
		text-decoration: none;
		box-shadow: 3px 3px 0 #10120f;
	}

	.github-link svg {
		width: 18px;
		height: 18px;
		fill: currentColor;
	}

	:global(.docs-article h1),
	:global(.docs-article h2),
	:global(.docs-article h3) {
		margin: 0;
	}

	:global(.docs-article h1) {
		margin: 0 0 16px;
		border-bottom: 2px solid #10120f;
		padding-right: 120px;
		padding-bottom: 20px;
		font-size: clamp(2.4rem, 7vw, 4.5rem);
		font-weight: 700;
		line-height: 0.95;
	}

	:global(.docs-article h2) {
		margin-top: 30px;
		margin-bottom: 10px;
		font-size: 1.05rem;
		font-weight: 700;
		line-height: 1.25;
	}

	:global(.docs-article h3) {
		margin-top: 22px;
		margin-bottom: 6px;
		font-size: 1rem;
		font-weight: 700;
		line-height: 1.3;
	}

	:global(.docs-article p),
	:global(.docs-article li) {
		color: #363d35;
		font-size: 1rem;
		line-height: 1.58;
	}

	:global(.docs-article p),
	:global(.docs-article ul),
	:global(.docs-article ol),
	:global(.docs-article table) {
		margin-top: 0;
		margin-bottom: 16px;
	}

	:global(.docs-article ol),
	:global(.docs-article ul) {
		padding-left: 1.15rem;
	}

	:global(.docs-article ul) {
		list-style-type: square;
	}

	:global(.docs-article ul li::marker) {
		color: #10120f;
		font-size: 0.82em;
	}

	:global(.docs-article li + li) {
		margin-top: 8px;
	}

	:global(.docs-article code) {
		border: 1px solid #dfe5dc;
		background: #f8faf6;
		padding: 0.08rem 0.24rem;
		font-size: 0.88em;
	}

	:global(.docs-article blockquote) {
		margin: 0 0 22px;
		border: 1px solid #dfe5dc;
		border-left: 4px solid #10120f;
		background: white;
		padding: 10px 14px;
		color: #363d35;
	}

	:global(.docs-article blockquote p) {
		margin: 0;
	}

	:global(.docs-article table) {
		display: block;
		width: 100%;
		overflow-x: auto;
		border-collapse: collapse;
		font-size: 0.92rem;
	}

	:global(.docs-article th),
	:global(.docs-article td) {
		border-bottom: 1px solid #dfe5dc;
		padding: 10px 12px;
		text-align: left;
		vertical-align: top;
	}

	:global(.docs-article th) {
		color: #10120f;
		font-weight: 700;
	}

	:global(.docs-article td:last-child),
	:global(.docs-article th:last-child) {
		text-align: right;
	}

	@media (max-width: 860px) {
		.docs-shell {
			grid-template-columns: 1fr;
		}

		.github-link {
			top: 24px;
			right: 24px;
		}
	}
</style>
