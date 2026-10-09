# 2026-10-08 — backoff & thundering herd lesson OPENED (text)

## What happened, in order
1. Learner, unprompted, described the reconciliation flow back: save request ID, send amount+user ID+request ID, reconciliation job "debates" the provider until the fund state is known — mostly correct skeleton. One garbled step at the end: "then we decide to 'double charged' them (not, just sending the payment request again) or not" — the two post-debate outcomes (provider has record → never resend; no record → safe retry, not a double-charge) were muddy. Probe posed on the two outcomes — UNANSWERED.
2. Learner asked what to learn next. Presented the map's options; recommended backoff & thundering herd (weakest edge node, natural continuation of the retry/reconciliation strand). Learner chose it.
3. Lesson opened. Probe Q1 posed: reconciliation job finds 50,000 stuck "unknown" payments; provider comes back online; what happens if all 50,000 retries fire the instant it recovers — what does the provider's day look like? UNANSWERED — learner ran /close.

## Evidence
- Reconciliation skeleton (request ID travels with the call; job queries provider by it): restated unaided, ~1 day — MECHANISM holding (name still avoided; consistent with the 2x name fade).
- Post-debate decision logic (has-record vs no-record outcomes): MUDDY at ~1 day — re-probe owed, fold into the 10-10..14 cold ping set.
- Backoff/thundering herd: nothing presented, nothing probed yet.

## Next session
- Re-open with Q1 (50,000 simultaneous retries at a just-recovered provider) as written above. It doubles as an intuition probe before any naming (thundering herd, backoff, jitter).
- Owed cold re-pings unchanged: 2026-10-10..14 — five-question audit, precondition + reconciliation-job names, provider-lookup-by-request-ID; ADD the two post-debate outcomes.

Model: Alvar (pi).
