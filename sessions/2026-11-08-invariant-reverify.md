# 2026-11-08 — sd/invariant re-verification (answered same day as ping)

## What happened

- Ping asked the outstanding sd/invariant re-verification (rule 2, oldest evidence 2026-10-23): what is an invariant, why isn't "we use a transaction" it, bonus charge-flow invariant.
- Learner answered same evening, unaided: "a rule that doesn't change, enforced at the write boundary" — definition + enforcement location recalled at 16d. Sharpened in reply: the state changes; the rule is what must always hold of it.
- Why-not-the-transaction: answered via external fail/timeout ("transaction sent outside could fail, results change") — true, but answers "why a transaction can't cover everything," not "why the transaction isn't the invariant." Re-presented the distinction: invariant = the rule; transaction = one guard; the rule must hold even where no guard reaches (receipt, reconciliation are other guards).
- Bonus charge-flow invariant: not recalled ("I don't remember"). Re-presented: no charge without a usage record, no record without a charge — balance and record move together. Presented only.

## Grade

- level: recalled (unaided) at 16d — definition half solid, mechanism distinction and charge-flow instance wobbly. No upgrade; node stays `recalled (unaided)`.
- Event appended 2026-11-08T23:24:28Z; view regenerated.

## Owed next

- sd/invariant re-probe ~2026-11-11..12 (mechanism-vs-rule distinction + charge-flow invariant, the two pieces that wobbled).
- Queue order vs existing: keyed-receipt unaided cold re-check 11-10..13 (rule 1 window open), timeout-unknown-state cold check ~11-15.

## Next node per routing

sd/keyed-receipt (rule 1 — owed unaided re-check window 2026-11-10..13).

Model: Alvar (pi).
