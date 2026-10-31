# 2026-10-26 — backoff depressurization reps, lesson closed

Model: Alvar (pi).

## What happened
- Lesson thread "backoff — depressurization reps" ran as planned (numeric reps, learner-requested).
- Q1 answered unaided with arithmetic: 1,000 clients on fixed 5s timer = 200 rps vs provider capacity 100 rps; rate constant forever (provider never gets quiet).
- Doubling timer (5-10-20-40-80s) walked to 12.5 rps — under capacity; pressure decays uncoordinated.
- Mid-lesson knot: learner pictured the crowd in lockstep and assumed a HEALTHY provider; reached for a queue ("group 100/sec, done in 10s") — independently invented throttling/queue-based load leveling. Coaching broke it: no central coordinator exists (each client owns only its own timer) and queues don't heal a sick dependency. Learner closed the loop himself: "I was always assuming healthy."
- Evidence event appended same day: sd/backoff explained (coached). Arithmetic unaided; the decentralized-clients insight needed coaching. The 10-25 PARTIAL gap (depressurization job) is now closed at explained level.
- Lesson ran from a sauna, by text thread, and worked — learner flagged this as a modality win.

## Evidence
- sd/backoff: explained (coached), delay 0d, event appended 2026-10-26, view regenerated.

## Learner-model updates (written to docs/learner.md)
- Numeric arithmetic reps (compute the actual rate) landed where prose hadn't; invented the queue pattern unprompted during one.
- Default-assumption trap: models dependencies as healthy unless told sick; teaching rule: ask "what state is the dependency in?" early.

## Owed / next
- Delayed re-check for sd/backoff: ~3-7 days after today → 2026-10-29 to 2026-11-02. Probe the 200-vs-12.5 contrast + "why does backoff protect a recovering dependency" cold.
- Next node per routing: sd/reconciliation-job (rule 2 — oldest node with no delayed evidence, last 2026-10-23), unless the backoff re-check comes due first (rule 1 wins).
