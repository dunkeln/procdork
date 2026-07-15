<script lang="ts">
	import '@excalidraw/excalidraw/index.css';
	import { onDestroy, onMount } from 'svelte';

	const assetPath = '/assets/procdork-architecture.excalidraw';
	let canvasHost: HTMLDivElement;
	let status = $state('Loading whiteboard...');
	let latestScene = $state<Record<string, unknown> | null>(null);
	let root: any = null;

	function sceneFrom(elements: unknown, appState: any, files: unknown) {
		const { collaborators, ...safeAppState } = appState ?? {};
		return {
			type: 'excalidraw',
			version: 2,
			source: 'https://excalidraw.com',
			elements,
			appState: safeAppState,
			files: files ?? {}
		};
	}

	async function saveScene() {
		if (!latestScene) {
			status = 'Nothing to save yet.';
			return;
		}

		status = 'Saving...';

		const response = await fetch('/api/whiteboard', {
			method: 'PUT',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify(latestScene)
		});

		if (!response.ok) {
			status = 'Save failed here. Download the scene and replace the asset file.';
			return;
		}

		status = 'Saved to web/static/assets/procdork-architecture.excalidraw';
	}

	function downloadScene() {
		if (!latestScene) return;

		const blob = new Blob([`${JSON.stringify(latestScene, null, 2)}\n`], {
			type: 'application/json'
		});
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = 'procdork-architecture.excalidraw';
		link.click();
		URL.revokeObjectURL(url);
	}

	onMount(async () => {
		const [react, reactDom, excalidraw, sceneResponse] = await Promise.all([
			import('react'),
			import('react-dom/client'),
			import('@excalidraw/excalidraw'),
			fetch(assetPath)
		]);

		const initialData = await sceneResponse.json();
		latestScene = initialData;
		root = reactDom.createRoot(canvasHost);
		root.render(
			react.createElement(excalidraw.Excalidraw, {
				initialData,
				onChange: (elements: unknown, appState: any, files: unknown) => {
					latestScene = sceneFrom(elements, appState, files);
					status = 'Unsaved changes';
				}
			})
		);
		status = 'Ready';
	});

	onDestroy(() => {
		root?.unmount();
	});
</script>

<svelte:head>
	<title>procdork whiteboard</title>
	<meta
		name="description"
		content="Repo-owned Excalidraw whiteboard for the procdork architecture narrative."
	/>
</svelte:head>

<section class="whiteboard-shell">
	<header class="whiteboard-toolbar">
		<div>
			<h1>Procdork whiteboard</h1>
			<p>{status}</p>
		</div>
		<div class="actions">
			<button type="button" onclick={saveScene}>Save</button>
			<button type="button" onclick={downloadScene}>Download</button>
		</div>
	</header>
	<div bind:this={canvasHost} class="canvas-host" aria-label="Procdork architecture Excalidraw canvas"></div>
</section>

<style>
	.whiteboard-shell {
		display: grid;
		grid-template-rows: auto 1fr;
		min-height: 100dvh;
		background: #f5f5f0;
		color: #171717;
	}

	.whiteboard-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		border-bottom: 1px solid #d8d4ca;
		background: #fffdf8;
		padding: 12px 16px;
	}

	h1,
	p {
		margin: 0;
	}

	h1 {
		font-size: 1rem;
		font-weight: 700;
	}

	p {
		color: #666;
		font-size: 0.84rem;
	}

	.actions {
		display: flex;
		gap: 8px;
	}

	button {
		border: 1px solid #cfc8ba;
		border-radius: 6px;
		background: #ffffff;
		color: #171717;
		cursor: pointer;
		font: inherit;
		font-size: 0.88rem;
		font-weight: 600;
		padding: 8px 12px;
	}

	button:hover {
		background: #f2eee5;
	}

	.canvas-host {
		min-height: 0;
	}

	@media (max-width: 640px) {
		.whiteboard-toolbar {
			align-items: stretch;
			flex-direction: column;
		}

		.actions {
			width: 100%;
		}

		button {
			flex: 1;
		}
	}
</style>
