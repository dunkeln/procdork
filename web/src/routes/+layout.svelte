<script lang="ts">
	import './layout.css';
	import logo from '$lib/assets/procdork-logo.png';
	import { Toaster } from '$lib/components/ui/sonner';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={logo} />
	<title>procdork</title>
	<meta
		name="description"
		content="procdork searches live web evidence for supplier procurement workflows through a server-side TinyFish connector."
	/>
</svelte:head>

<main class="min-h-dvh bg-background text-foreground">
	{@render children()}
	<Toaster />
</main>
