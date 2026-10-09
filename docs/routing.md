# Routing — where to go next

> Purpose: no session ever ends on "learner picks." The next node is **computed**
> from the maps, not chosen from a blank field. The learner can always override —
> an override is data (record it), not disobedience.
> Inputs: every file in `maps/`, the owed-ping queue in `docs/current-state.md`,
> and `docs/goal.md`. Method: computed by the agent at session start by reading
> those files. No code. If this rule survives a few weeks of use, it earns
> automation (second-need rule).

## The scoring rule (apply in order — first match wins)

1. **Owed recall pings.** Overdue or due-today retention checks always win.
   Retention beats novelty; a faded node re-taught late costs more than a new node.
2. **Fading `known` nodes.** Any node marked `known` whose latest evidence is the
   oldest across all maps gets a re-verification probe. Delay is a dimension —
   knowledge rots (epistemic axis) and memory rots (mastery axis); check both.
3. **`edge` nodes, ranked by unblock-count.** For each edge node, count how many
   `blocked`/`unknown` nodes name it as a prerequisite (explicitly, or by the
   agent's dependency judgment recorded in the map). Teach the one that unlocks
   the most. Ties break toward the current goal in `docs/goal.md`, then toward
   the node with a concrete anchor in the learner's own projects (thesis H8).
4. **`unprobed` strands.** Open with a probe, not a lesson. Anchor the probe to
   whichever of the learner's projects exercises the strand (see the anchors
   table in the relevant map).

## Tie-breakers and overrides

- If two maps compete (multi-discipline future), weight by the current goal in
  `docs/goal.md`; interleave owed pings across maps (thesis H10).
- Learner override: honor it immediately, then record it in the session log and
  note whether routing's pick was wrong (evidence about the rule) or just
  different (evidence about the learner's interest — feed `docs/learner.md`).
- If routing produces a pick the learner has refused twice, stop proposing it and
  say why. Annoyance is evidence about the learner, not disobedience (spine).

## Session-close requirement

Every `/close` must end with: **"next node per routing: `<node>` (reason: `<which
rule fired>`)"** written into `docs/current-state.md` and `sessions/NEXT-BOOT.md`.
A close that ends on "learner picks" is drift — the handoff's drift test applies.

## What this rule deliberately does NOT do

- It does not sequence by any external curriculum. Sequencing inputs are the
  dependency graph, the learner's projects, and `docs/goal.md` — nothing else.
- It does not maximize novelty. Unprobed strands rank *last*, because
  consolidating the edge beats opening new fronts (thesis H2).
- It does not ping. Routing decides *what*; the learner's contact preferences
  (docs/goal.md standing constraint 1) decide *whether the agent speaks first*.
