<script lang="ts">
	import { page } from '$app/state';
	import { ArrowUpRight } from '@lucide/svelte';

	const docsPages = [
		{ href: '/docs', title: 'Architecture' },
		{ href: '/docs/cost-forecast', title: 'Cost forecast' },
		{ href: '/docs/how-to', title: 'How to?' },
		{ href: '/docs/examples', title: 'Examples' },
		{ href: '/docs/benchmarks', title: 'Benchmarks' },
		{ href: '/docs/decisions', title: 'Decision boundary' }
	];
	const currentPath = $derived(page.url.pathname);
</script>

<nav class="docs-nav" aria-label="Docs">
	{#each docsPages as item (item.href)}
		<a class:active={currentPath === item.href} href={item.href}>{item.title}</a>
	{/each}
	<a class="site-link" href="/sessions">Go to site <ArrowUpRight /></a>
</nav>

<style>
	.docs-nav {
		position: sticky;
		top: 32px;
		display: flex;
		flex-direction: column;
		gap: 10px;
		align-self: start;
	}

	a {
		border: 2px solid transparent;
		background: transparent;
		padding: 10px 13px;
		color: #3f443d;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		text-decoration: none;
		box-shadow: inset 0 -1px 0 #10120f33;
	}

	.site-link {
		margin-top: 8px;
		display: inline-flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		border-color: #10120f;
		background: #9bd2f2;
		color: #10120f;
		box-shadow: 3px 3px 0 #10120f;
	}

	.site-link :global(svg) {
		width: 14px;
		height: 14px;
	}

	a:hover,
	a.active {
		border-color: #10120f;
		background: #f3eee7;
		color: #10120f;
		box-shadow: 3px 3px 0 #10120f;
	}

	.site-link:hover {
		background: #8bc7eb;
	}

	@media (max-width: 860px) {
		.docs-nav {
			position: static;
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		}
	}
</style>
