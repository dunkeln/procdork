<script lang="ts">
	const repeatedVolume = [
		{ label: 'runs', value: 64, note: 'same questions, repeated' },
		{ label: 'calls', value: 192, note: 'all completed' }
	];

	const stableFacts = [
		{ label: 'sessions', value: 5, note: 'same answer every time', y: 54 },
		{ label: 'messages', value: 8, note: 'same answer every time', y: 90 },
		{ label: 'events', value: 46, note: 'same answer every time', y: 126 },
		{ label: 'sources', value: 29, note: 'same answer every time', y: 162 }
	];
	const repeatedBars = [...repeatedVolume, ...stableFacts];

	const adversarial = [
		{ label: 'workflows', value: 24, note: 'completed messy runs' },
		{ label: 'MCP calls', value: 313, note: 'tools used under pressure' },
		{ label: 'tool errors', value: 26, note: 'absorbed without fake answers' }
	];

	const calls = [
		{ label: 'typical', value: 13 },
		{ label: 'heavy', value: 28 }
	];

	const cachedContext = 90.1;
	const freshContext = 9.9;

	let activePoint = $state(repeatedVolume[0]);
</script>

<div class="benchmark-story">
	<header class="hero">
		<h1>Did the harness keep the answer steady?</h1>
		<p>
			Claude can take different paths, use different words, and hit rough data. The facts should
			still land in the same place.
		</p>
	</header>

	<section class="plain">
		<h2>Test 1: ask the same thing again and again.</h2>
		<p>
			Like asking 10 people to count the same jar of coins. They may count in different orders, but
			the number should not change.
		</p>
	</section>

	<section class="plot-card" aria-labelledby="repeated-heading">
		<div>
			<h2 id="repeated-heading">Repeated-answer run</h2>
			<p>
				Across 64 runs and 192 calls, the harness kept returning the same core facts: 5 sessions, 8
				messages, 46 events, and 29 cited sources.
			</p>
		</div>

		<div class="bar-plot" role="img" aria-label="Observed benchmark counts">
			<div>
				{#each repeatedBars as point}
					<button
						class:active={activePoint.label === point.label}
						type="button"
						style={`--h:${Math.max(10, (point.value / 192) * 100)}%`}
						onmouseenter={() => (activePoint = point)}
						onfocus={() => (activePoint = point)}
					>
						<span></span>
						<small>{point.label}</small>
					</button>
				{/each}
			</div>
		</div>

		<p class="readout">
			<strong>{activePoint.value} {activePoint.label}</strong>
			<span>{activePoint.note}</span>
		</p>
	</section>

	<section class="plain">
		<h2>Test 2: give it messy data and see if it lies.</h2>
		<p>
			This is the adversarial test for sanity. Some evidence was intentionally missing or stale. The
			harness evidenced enough for Claude to say “I don’t know” instead of pretending.
		</p>
	</section>

	<section class="grid">
		<div class="plot-card">
			<h2>Adversarial run</h2>
			<div class="stat-stack">
				{#each adversarial as item}
					<div>
						<span class="stat-line"><strong>{item.value}</strong> {item.label}</span>
						<small>{item.note}</small>
					</div>
				{/each}
			</div>
		</div>

		<div class="plot-card">
			<h2>Tool-call pressure</h2>
			<svg
				viewBox="0 0 320 160"
				role="img"
				aria-label="Typical workflow made 13 calls, heavy workflow made 28 calls"
			>
				<line x1="32" y1="122" x2="292" y2="122" />
				{#each calls as point, index}
					<g>
						<rect
							x={72 + index * 128}
							y={122 - point.value * 3.2}
							width="56"
							height={point.value * 3.2}
						/>
						<text x={100 + index * 128} y={112 - point.value * 3.2}>{point.value}</text>
						<text x={100 + index * 128} y="146">{point.label}</text>
					</g>
				{/each}
			</svg>
			<p>The busy run used more tools, but it still stayed inside the evidence boundary.</p>
		</div>
	</section>

	<section class="plot-card token-card">
		<div>
			<h2>Context reuse is the useful signal.</h2>
			<p>
				Most of the context was reused over getting rebuilt. The harness provided stable retrieved
				context, so Claude could keep answering from cached session material instead of re-reading
				the world each turn.
			</p>
		</div>

		<div
			class="token-stats"
			aria-label={`${cachedContext} percent cached context and ${freshContext} percent fresh context`}
		>
			<span class="cached">
				<strong>{cachedContext}%</strong>
				<small>cached context</small>
			</span>
			<span class="fresh">
				<strong>{freshContext}%</strong>
				<small>fresh context</small>
			</span>
		</div>
	</section>

	<section class="plain closing">
		<h2>The simple score</h2>
		<p>
			A good run gets more useful with each turn. It cites where facts came from, admits what is
			missing, avoids fake certainty, and does not keep repeating the same search unless new
			evidence appears.
		</p>
	</section>
</div>

<style>
	.benchmark-story {
		color: #10120f;
	}

	.hero {
		border-bottom: 2px solid #10120f;
		padding-bottom: 22px;
	}

	.readout span,
	.stat-stack small,
	.token-stats small {
		color: #747c70;
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
	}

	h1,
	h2,
	p {
		margin-top: 0;
	}

	h1 {
		max-width: 12ch;
		margin-bottom: 18px;
		font-size: clamp(2.7rem, 8vw, 5.25rem);
		font-weight: 800;
		letter-spacing: 0;
		line-height: 0.92;
	}

	h2 {
		margin-bottom: 8px;
		font-size: 1.1rem;
		font-weight: 800;
	}

	p {
		max-width: 58rem;
		color: #363d35;
		font-size: 1rem;
		line-height: 1.65;
	}

	.plain,
	.plot-card {
		margin-top: 28px;
	}

	.plot-card {
		border: 1px solid #10120f;
		background: #fbfcfa;
		padding: 18px;
		box-shadow: 5px 5px 0 #10120f;
	}

	.bar-plot {
		margin-top: 16px;
	}

	.bar-plot > div {
		display: grid;
		grid-template-columns: repeat(6, minmax(52px, 1fr));
		align-items: end;
		height: 190px;
		gap: 10px;
		border-bottom: 2px solid #10120f;
	}

	.bar-plot button {
		display: grid;
		grid-template-rows: 1fr auto;
		height: 100%;
		border: 0;
		background: transparent;
		color: #10120f;
		cursor: pointer;
		font: inherit;
		font-weight: 800;
	}

	.bar-plot button span {
		display: block;
		align-self: end;
		height: var(--h);
		border: 1px solid #10120f;
		background: #10120f;
	}

	.bar-plot button.active span,
	.bar-plot button:hover span,
	.bar-plot button:focus-visible span {
		background: #8fcdf0;
	}

	.bar-plot button:focus-visible {
		outline: 0;
	}

	.bar-plot small {
		margin-top: 6px;
		color: #747c70;
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
		font-size: 0.7rem;
	}

	.readout {
		margin: 14px 0 0;
	}

	.readout strong,
	.readout span {
		display: block;
	}

	.grid {
		display: grid;
		grid-template-columns: minmax(0, 0.8fr) minmax(0, 1fr);
		gap: 18px;
	}

	.stat-stack {
		display: grid;
		gap: 10px;
	}

	.stat-stack div {
		border-top: 1px solid #dfe5dc;
		padding-top: 12px;
	}

	.stat-stack strong {
		font-size: 2.15rem;
		line-height: 1;
	}

	.stat-stack small {
		display: block;
	}

	.stat-line {
		display: inline-flex;
		align-items: baseline;
		gap: 10px;
		color: #10120f;
	}

	svg {
		width: 100%;
		height: auto;
		margin-top: 8px;
	}

	svg line {
		stroke: #10120f;
		stroke-width: 2;
	}

	svg rect {
		fill: #10120f;
	}

	svg text {
		fill: #363d35;
		font:
			700 13px ui-monospace,
			SFMono-Regular,
			Menlo,
			Monaco,
			Consolas,
			monospace;
		text-anchor: middle;
	}

	.token-card {
		display: grid;
		grid-template-columns: minmax(0, 0.75fr) minmax(240px, 1fr);
		gap: 18px;
		align-items: center;
	}

	.token-stats {
		display: grid;
		grid-template-columns: 1fr 0.7fr;
		gap: 10px;
	}

	.token-stats span {
		display: grid;
		align-content: center;
		min-height: 112px;
		border: 1px solid #10120f;
		padding: 16px;
		color: #10120f;
		background: white;
	}

	.token-stats .cached {
		background: #10120f;
		color: white;
	}

	.token-stats .cached small {
		color: #dfe5dc;
	}

	.token-stats strong {
		font-size: clamp(1.3rem, 4vw, 2.4rem);
		line-height: 1;
	}

	.closing {
		border-top: 1px solid #dfe5dc;
		padding-top: 22px;
	}

	@media (max-width: 720px) {
		.grid,
		.token-card {
			grid-template-columns: 1fr;
		}

		.plot-card {
			padding: 14px;
		}
	}
</style>
