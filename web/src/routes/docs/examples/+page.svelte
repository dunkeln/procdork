<svelte:head>
	<title>Examples | procdork docs</title>
	<meta name="description" content="Useful prompt shapes for supplier discovery runs." />
</svelte:head>

<h1>Examples</h1>

<video
	class="example-video"
	src="/assets/videos/example-usecase.mp4"
	autoplay
	controls
	playsinline
	preload="metadata"
>
	<track kind="captions" />
</video>

<p>Sample prompts to try with Procdork.</p>

<h2>Supplier evidence coverage</h2>
<ul>
	<li>Which suppliers look most supported by evidence, and where should I be careful?</li>
	<li>What can I safely claim about suppliers from the current data?</li>
</ul>

<h2>Evidence gaps</h2>
<ul>
	<li>Show me where evidence is strong, thin, or missing across the supplier workflow.</li>
	<li>What is missing before we can confidently rank suppliers?</li>
</ul>

<h2>Source concentration</h2>
<ul>
	<li>Which source domains carry the most evidence, and are any overrepresented?</li>
	<li>What sources should I inspect first if I want to verify supplier claims?</li>
</ul>

<h2>Tool reliability</h2>
<ul>
	<li>Which tools are doing the most work, and where are they failing?</li>
	<li>Show tool activity by status.</li>
</ul>

<h2>Session heatmap</h2>
<ul>
	<li>Show tool usage by session and tell me which sessions look unusual.</li>
	<li>Where do tool errors cluster by session?</li>
</ul>

<h2>Time trends</h2>
<ul>
	<li>Are recent sessions getting faster or slower?</li>
	<li>What changed recently?</li>
</ul>

<h2>Judge evals</h2>
<ul>
	<li>Which judge dimensions are improving, drifting, or getting worse?</li>
	<li>Where are eval scores weakest right now?</li>
</ul>

<h2>Treatment comparison</h2>
<ul>
	<li>Are any treatments consistently outperforming the others?</li>
	<li>Compare grounding, consistency, and completeness across treatments.</li>
</ul>

<h2>Category mix</h2>
<ul>
	<li>What categories dominate the current data, and which ones are empty?</li>
	<li>Show category mix across sessions.</li>
</ul>

<h2>Freshness</h2>
<ul>
	<li>What looks fresh, what looks stale, and what changed recently?</li>
	<li>Which pipeline runs look stale?</li>
</ul>

<h2>Demo-safe answer</h2>
<ul>
	<li>Give me the strongest supported claim and the biggest caveat.</li>
	<li>What should I not claim based on the current data?</li>
</ul>

<style>
	.example-video {
		display: block;
		width: 100%;
		margin-bottom: 24px;
		border: 1px solid #10120f;
		box-shadow: 5px 5px 0 #10120f;
		background: #10120f;
	}
</style>
