# 2026-11-08 — sd/timeout-unknown-state re-probe (migration-verification ping)

- Trigger: learner asked for one recall ping "for migration verification" — an explicit override pulling the rule-1 re-probe (scheduled 11-09..10) one day early. Override recorded as data; routing's pick was not wrong, just scheduled.
- Q1: outside call (card charge) timed out — what states could it be in? Answer, unaided: **executed, pending, failed.** Correct — this is the enumeration that evaporated at 5d on 11-07. Now recalled unaided at 1d post re-presentation.
- Event appended (recalled, delay_days 1, unaided). View regenerated.
- Q2: which state do you assume as caller? Answer: **pending** — correct (holding the question open, not concluding).
- Q3: do you fire the charge again? Answer, unaided: **no blind retry** — read the receipt saved before the send, query provider status by the request ID saved at send start, hand to the reconciliation job for periodic checks. Full recovery move intact; keyed-receipt + reconciliation-job vocabulary surfaced unprompted.
- Verdict: RETENTION RESTORED at 1d post-failure. Events appended (recalled + applied, both unaided, delay_days 1). Next cold check suggested ~11-15 (7d). Owed queue after this exchange: sd/invariant re-verification (still unanswered from 11-08); sd/keyed-receipt cold full-pattern re-check 11-10..13.
- Close (/close 11-08): events already appended live; view regenerated; docs/learner.md gained one row (faded lists re-arm fast after one re-presentation); decision-log untouched (no approach change); sessions/NEXT-BOOT.md written fresh (next node per routing: sd/keyed-receipt, rule 1, window opens 11-10). No git commit — nightly cron.
- Model: Alvar (pi).
