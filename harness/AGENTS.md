# The dork evals harness

Read [AGENTS.md](../AGENTS.md) to learn yourself.

### What's our push?

Standard ETL/ELT use heavy and dedicated compute building standalone infra to serve the product.
The barrier is the additional infra. We are Occam's razor and keeping close to fundamentals. We account for noise in production as well.

The rubric driving our idea:

+ Amdahl's Law (write only measured or falsifiable systems-design evidence into [perf memory](../.codex/memories/perf.md); contrast against traditional ELT; human time is ∞)
+ Scale economics
+ metrics fanout to mitigate fallacy highlighted in Goodhart's law; keep this to decision-useful views over the same raw evidence, not new event/schema sprawl
+ Elastic & deterministic core; capture noisy production edges as inputs, then keep replay deterministic
+ Agent usage tax to be thought of
  - i/p tokens vs o/p tokens
  - agent-in-the-loop burnouts
  - agent autonomy in seams & critical areas
+ maintenance tax (as a maintainer)
+ weathering harness and loop engineering
+ separation of concerns, clear boundaries between functional pieces (pipeline engineering, data science, MCP etc. in their defined regions)


### Build with caution - be conservative

Open Knowledge Format (OKF) standardizes the knowledge surface by organizing concepts into individual Markdown files
within a unified directory structure. Each file uses structured YAML metadata for categorization and standard
relative links to map relationships, enabling AI agents to trace dependencies and retrieve context without heavy database indexing.
Do not turn OKF into a parallel database or schema regime unless the harness proves Markdown/YAML is insufficient.
