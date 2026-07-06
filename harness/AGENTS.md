# The dork evals harness

Read [AGENTS.md](../AGENTS.md) to learn yourself.

### Separation of concerns

- Revise reusable stateless functions in [utils](utils/)
- connectors/adapters iterated and built in [connectors](connectors/)
- core runtime in [core](core/)

### What's our push?

Standard ETL/ELT use heavy and dedicated compute building standalone infra to serve the product.
The barrier is the additional infra. We are Occam's razor and keeping close to fundamentals.

The rubric driving our idea:

+ Amdahl's Law
+ Scale economics
+ metrics fanout to mitigate fallacy highlighted in Goodhart's law
+ Elastic & deterministic core
+ Agent usage tax
  - i/p tokens vs o/p tokens
  - agent-in-the-loop burnouts
  - agent autonomy in seams & critical areas
+ maintenance tax
+ weathering harness and loop engineering
