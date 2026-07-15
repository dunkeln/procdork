# Procdork architecture

Procdork is a production-oriented harness for procurement intelligence. It
preserves source evidence, turns messy operational work into governed analytical
surfaces, and gives client agents the same reviewed data that operators use.

The intended use is simple: share this page with a client or executive, let them
paste the link into Claude or another agent, and ask progressive questions about
the system. The page is written as a compact knowledge surface, not a slide
deck. It should let the reader move from "what is this?" to "what evidence do
you have?" to "what would this do in my environment?"

## The operating idea

Procurement work already happens in the places operators live. For Waystation,
that place is the inbox. For Procdork, the equivalent surface is the client
agent session: Claude, Codex, Cursor, or any other MCP-capable environment.

The goal is not to make another dashboard that operators have to remember to
open. The goal is to make the reviewed data, source evidence, charting rules,
and institutional context available inside the cloud session where the user is
already asking questions.

That changes the coordination model. Instead of spreading business meaning
across source systems, warehouse objects, dashboards, docs, and agent prompts,
Procdork compresses the operating loop into one reviewed harness surface.

For this slice:

```text
7 governed functions / 1 reviewed surface = about 7x operator surface power
```

That is not a staffing or wall-clock savings claim. It is a coordination-tax
claim: fewer independently maintained surfaces for the same analytical loop.

## What the environment contains

Procdork has three production-facing layers.

### 1. Source and event capture

The environment accepts source evidence from procurement-adjacent systems:
layout-aware document parsing, vendor document traces, application events,
Postgres-backed interaction history, and telemetry. These are not treated as
presentation fixtures. They are preserved as source evidence so later analytical
answers can point back to what produced them.

### 2. Transform and intelligence layer

The harness promotes durable evidence into queryable analytical surfaces. dbt
models define executable facts. Object storage and warehouse-compatible
analytics provide the durable data path. The operator-owned transform layer is
where messy evidence becomes stable procurement intelligence: supplier claims,
source coverage, confidence, conflicts, benchmark results, and workflow health.

### 3. Agent and knowledge layer

MCP exposes the reviewed analytics to client agents. OKF carries the meaning:
business caveats, chart eligibility, interpretation rules, provenance notes, and
when a result is not broad enough to support a decision.

This division matters:

```text
dbt determines the answer
OKF explains the answer
MCP delivers the answer
```

The agent does not need to guess what a table means or invent chart rules. It
can read the reviewed knowledge surface and query the governed data.

## What was produced

The project produced a working vertical system, not just a concept.

- A web application surface for procurement workflows and operator-facing
  interaction.
- Ingestion microservices that capture vendor and application evidence as event
  traces.
- A harness that loads evidence, runs transforms, and exposes stable marts.
- dbt models for repeatable analytical surfaces.
- OKF knowledge files that explain how agents should interpret those surfaces.
- MCP tools and chart rendering so Claude and other agents can query and
  visualize the data.
- Evaluation and pressure-test evidence showing how the harness behaves when
  data is missing, stale, or incomplete.

The important destination is stable behavior under inquiry. A client agent
should be able to ask about supplier evidence, source reach, workflow health,
benchmark tradeoffs, or chartable summaries without rebuilding context from
scratch.

## What the harness proved

The harness has measured evidence, but the claims stay bounded.

Repeated-answer tests showed that agents could ask the same analytical questions
through different query paths and still land on the same facts. In adversarial
data-readiness tests, the harness answered from available evidence and refused
to invent unsupported supplier rankings, confidence measures, or conflict
results.

The strongest measured reuse signal is context reuse: across 24 completed
adversarial workflows, 90.1% of cumulative input tokens came from cached input.
Only 9.9% was fresh input. That suggests the reviewed context can be reused
across repeated analytical workflows instead of being reassembled every time.

The harness also provides an operator-surface scaling law:

```text
marginal_operator_burden =
  new_reviewed_surface_changes / new_workflows_served
```

The theory is conservative. Infrastructure limits do not disappear. Operator
judgment does not disappear. The claim is that a reviewed surface can serve more
workflows, agents, and analytical questions before another review cycle is
needed.

## Day-zero deployment posture

Procdork is deployable once the source environment is configured. Day zero does
not mean the system knows a customer's suppliers before sources exist. It means
the operating pattern is already in place:

- connect the source systems
- preserve raw evidence
- run the transform harness
- expose reviewed marts
- attach OKF interpretation
- let client agents query through MCP
- evaluate outputs against evidence boundaries

That is the value of the harness: the deployment starts from a stable analytical
operating loop rather than from a blank integration project.

## How a client agent should use this page

This page is meant to be queried progressively.

Start with orientation:

```text
What is Procdork, and what operating problem does it solve?
```

Then ask for the system boundary:

```text
Explain the source, transform, knowledge, and MCP layers.
```

Then ask for proof:

```text
What measured evidence supports the stability of the harness?
```

Then ask for business meaning:

```text
How does operator surface power reduce coordination tax?
```

Then ask for deployment fit:

```text
What would need to be configured on day zero for this to work in a procurement
environment?
```

The expected behavior is progressive disclosure. The agent should answer the
first question simply, then use the later questions to expose more detail about
evidence, deployment, evaluation, and business impact.

## What this means for a procurement team

The business value is not that every decision becomes automatic. The value is
that the same reviewed surface can carry source evidence, transformations,
institutional meaning, charting rules, provenance, and replay evidence into the
agent session where the user is already working.

That makes coordination tax visible. If a supplier claim is thin, the system can
say it is thin. If a certification field has conflicts, the system can localize
the conflict. If source coverage is broad but structured extraction is narrow,
the system can show the drop-off. If a chart is unsupported, the knowledge layer
can steer the agent toward a valid shape.

The final state is not a prettier dashboard. It is a procurement intelligence
surface that can be queried, audited, and improved without losing the source
evidence that made the answer possible.
