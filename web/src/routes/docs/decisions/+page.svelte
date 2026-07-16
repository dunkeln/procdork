<script lang="ts">
	import { File, Folder } from '@lucide/svelte';
</script>

<svelte:head>
	<title>Decision boundary | procdork docs</title>
	<meta
		name="description"
		content="How simulated procurement operators pressure decision quality."
	/>
</svelte:head>

<h1>Decision boundary</h1>

<p>
	Building on the core idea, human-in-the-loop is a critical step in agentic workflows. Here it is
	referenced as Operator-in-the-Loop (OITL). The distinction is important because it defines humans
	equipped with agents at execution gates, becoming operators.
</p>

<h2>Structural boundaries</h2>

<p>
	OITL is defined at the Data, ML and forward-deployed boundaries via dbt SQL transformations,
	notebooks-based discovery and product knowledge as the respective surfaces for the operator to
	maintain execution.
</p>

<p>
	A positive side-effect from such structure and the product intelligence notes (OKF) is organic and
	evidence-led schema evolution as surfaced knowledge reveals recurring questions, gaps and useful
	analytical shapes. This helps an operator iterate existing transforms over redesigning from scratch
	with no context. That means the database structure doesn't prescribe a STAR schema, Constellation
	schema or Snowflake schema. Adoption ties with a justification for it.
</p>

<img
	class="boundary-image"
	src="/assets/images/harness-boundary.png"
	alt="Sketch of the harness boundary showing shared scheduling policies, extraction and loading, transformation surface plus institutional information, and the MCP boundary."
/>

The ELT pipeline, with the harness readoption, is packaged as one compute unit. That makes it easier
to scale vertically, in contrast to horizontally maintained distributed systems.

<div class="file-tree" aria-label="Harness file tree">
	<div class="tree-entry tree-root"><Folder size={16} aria-hidden="true" /> harness</div>
	<div class="tree-children">
		<div class="tree-entry"><File size={16} aria-hidden="true" /> extraction.py</div>
		<div class="tree-entry"><File size={16} aria-hidden="true" /> load.py</div>
		<div class="tree-entry"><File size={16} aria-hidden="true" /> cli.py</div>
		<div class="tree-entry"><Folder size={16} aria-hidden="true" /> transforms/</div>
		<div class="tree-entry"><Folder size={16} aria-hidden="true" /> connectors/</div>
		<div class="tree-entry"><Folder size={16} aria-hidden="true" /> evaluators/</div>
		<div class="tree-entry"><Folder size={16} aria-hidden="true" /> knowledge/</div>
		<div class="tree-entry"><Folder size={16} aria-hidden="true" /> mcp_app/</div>
		<div class="tree-entry"><File size={16} aria-hidden="true" /> mcp_server.py</div>
	</div>
	<div class="tree-entry tree-root">
		<Folder size={16} aria-hidden="true" /> notebooks/ <em>independent exploration</em>
	</div>
</div>

<h2>Development Decisions</h2>

<p>The development of the harness bears few fundamental principles:</p>

<ul>
	<li>
		<strong>Dependency Injection</strong><br />
		<em>
			The harness is its own stable boundary. External adapters and sources shouldn't alter the
			harness logic. That keeps it stable. Dependency injection is a step from class inheritance
			that compounds to unnecessary code bloat and harness maintainability.
		</em>
	</li>
	<li>
		<strong>YAGNI</strong><br />
		<em>
			You-Aren't-Gonna-Need-It is enforced over development iterations as a guardrail against
			bloated harness code, enabling efficient readability, maintenance and debugging.
		</em>
	</li>
	<li>
		<strong>Anchoring Bias</strong><br />
		<em>
			Coding agents and operators share a common failure: the first stated fact, target, or framing
			can become heavier than the evidence that follows. The development process treats early
			assumptions as visible assumptions, not implementation truth, so later evidence can revise,
			contradict, or narrow the direction instead of orbiting the original anchor.
		</em>
	</li>
</ul>

<h2>Rabbit holes I didn't scope here</h2>

<ul>
	<li>
		MCP apps are a powerful way to have stateless widgets served as BI dashboards and charts. I've
		kept it for future work to understand scope and requirements before execution. Recommended <u
			><a href="https://www.youtube.com/watch?v=sAOBXCDiDOs&t=970s">watch.</a></u
		>
	</li>
	<li>
		Cache invalidation and busting. It's partially handled by Claude and ChatGPT, but it's not
		perfect. Mature cache control strategies are first on the TODO list.
	</li>
	<li>Mature RBAC, just doesn't fit this objective.</li>
	<li>
		Perfecting backfills into dbt. It is justified only in real deployments for product in services.
	</li>
	<li>Self-healing operations. Redirected time to build the everything else 💀.</li>
	<li>
		Automatically syncing OKF Knowledge to schema diffs. It's a simple fix with a pre-commit hook for
		agents. Didn't make skills another topic to address, to maintain brevity.
	</li>
</ul>

<style>
	.boundary-image {
		display: block;
		width: 100%;
		margin: 24px 0;
		border: 1px solid #dfe5dc;
		background: white;
	}

	.file-tree {
		margin: 24px 0;
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
	}

	.tree-entry {
		display: flex;
		align-items: center;
		gap: 8px;
		min-height: 28px;
	}

	.tree-root {
		font-weight: 600;
	}

	.tree-root em {
		font-weight: 400;
	}

	.tree-children {
		margin-left: 7px;
		padding-left: 24px;
		border-left: 1px solid #dfe5dc;
	}
</style>
