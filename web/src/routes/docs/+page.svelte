<svelte:head>
	<title>procdork docs</title>
	<meta
		name="description"
		content="Documentation for the procdork supplier procurement workflow."
	/>
</svelte:head>

<h1>The data & evals harness</h1>

<blockquote>
	<p>
		For full LLM-readable project context, read
		<a href="/llms-full.txt">https://procdork.vercel.app/llms-full.txt</a>.
	</p>
</blockquote>

<p>
	The harness is production-oriented and developed from insights over iterations with a thin slice
	of real procurement work.
</p>

<h2>Core ideology</h2>

<p>
	Coding agents are as important to infrastructure as the system of microservices. With agents in
	the loop, software development accelerates when it is guardrailed against bias with better
	context. On the opposing end, it is riskier for any agent to autonomously build execution that
	requires governance or reconciliation.
</p>

<p>Model evals become more important when agents are part of the workflow.</p>

<h2>Simulation to harness</h2>

<p>
	For this harness to align as an embedded service instead of another dashboard, I built a thin
	working slice for discovery on publicly available supplier information: MOQs, RFx, lead-time
	evidence, and related sourcing signals. Simulation sits outside the harness itself; it is the
	pressure-test layer used to exercise the harness like real operators would. The application uses
	web fetch and browser subagent work to scrape information into structured shape. MIME formats such
	as PDFs, docs, and spreadsheets are sent as background tasks to a document-layout-aware Python
	microservice. The service returns source-claim-like structured evidence with URL, retrieved_at,
	MIME hint, confidence, and extraction method. The multi-step chat runtime uses surfaced evidence,
	enriched responses, and an optional follow-up for drafting supplier email.
</p>

<p>
	All event data is flushed to a PostgreSQL backend served by Neon. The app is stateless, with the
	database as source of truth. That gives two surfaces: integrity metrics for evaluations and
	analyses, and system health metrics.
</p>

<h2>Data processing workflow</h2>

<p>
	This data processing and evaluation harness does not replace data vendors like Snowflake or
	Databricks. It propagates the same workflow patterns into a thinner decision-making surface:
	business intelligence, application health, product behavior over time, and related analytical
	context.
</p>

<p>It adopts the standard ELT pattern: Extract, Load, Transform.</p>

<h3>Extraction and loading</h3>
<p>
	Extraction is a dltHub extraction on captured structured data from sources. That gives the
	harness a boring, replayable loading boundary instead of custom one-off scripts for every source.
	The useful part is the contract: extractors pull source events and documents into a durable shape,
	keep provenance close to the payload, and let the downstream transform layer decide what becomes
	analytical truth.
</p>

<p>
	dltHub also matches the ELT posture. The system can load partial or messy source records without
	blocking on a perfect schema, then use dbt and SQL transforms to promote stable marts later.
	Procurement source quality is uneven, so the extractor should preserve what happened and when; the
	transform layer should decide confidence, conflicts, and usefulness.
</p>

<h3>Data modeling for the team</h3>

<p>
	The transformation layer is the most human-operator focused boundary. SQL transformations surface
	data intelligence, but the effective shift comes from pairing them with a second brain: markdown
	knowledge that carries business caveats, contextual weight, and representation rules for promoted
	dbt marts. This is the knowledge layer.
</p>

<ul>
	<li>Agents can crawl file systems and markdown, reducing chat context bloat.</li>
	<li>Markdown is forgiving and avoids hundreds of lines of plumbing for many query changes.</li>
	<li>Business intelligence evolves forward-deployed with client needs.</li>
	<li>New maintainers inherit enriched context on day zero.</li>
	<li>Non-technical members can contribute to the second brain.</li>
</ul>

<p>
	<strong>TL;DR</strong> on the knowledge layer. The points above lead to the adoption of OKF, a markdown
	format. OKF shines where maintenance for vector embeddings becomes costly. It was first established
	by Andrej Karpathy as "llm wiki" and later adopted in production by Google BigQuery, now borrowed here
	too. This keeps knowledge readable while being faster and far less convoluted to iterate.
</p>

<p>More material:</p>

<ul>
	<li>
		<u>
			<a
				href="https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing"
				>Google's Article</a
			>
		</u>
	</li>
	<li>
		<u>
			<a href="https://www.youtube.com/watch?v=MY9F9K7wWX4">A quite useful video</a>
		</u>
	</li>
</ul>

<h3>Surfacing analytics</h3>

<p>
	Analytics is most useful when it surfaces where active work is visited the most, Claude or OpenAI
	chats, so this transport layer distinction matters.
</p>

<p>
	Instead of a BI tool, hosted dashboard, or scheduled report, information is served through MCP
	apps. MCP apps can carry transient widgets and functionality inside Claude or OpenAI chats. The
	user does not have to step outside the session to explore and return to reason with the client
	agent.
</p>

<p>
	<strong>The entire harness is a deterministic pipeline.</strong> The data modeling surface is where
	an operator, optionally with their agent, analyzes and promotes interpretable data, reducing the blast
	radius of unsupervised agent execution.
</p>
