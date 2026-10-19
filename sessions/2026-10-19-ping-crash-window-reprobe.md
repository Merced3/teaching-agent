# 2026-10-19 — ping: crash-window-in-payment-flow re-probe

Unprompted ping (routing rule 1: owed recall pings). Re-ask of the node that faded
2026-10-17 at ~11 days ("I don't know of a specific crash window" in the payment flow).

**Learner answer (unaided):** window is between the start of the provider call (keyed
receipt saved atomically) and the crash before knowing the call's outcome; the keyed
receipt stored the request ID, so the reconciliation job can check later. "The request
ID and keyed receipt keeps us safe from that crash."

**Grade:** recalled unaided, ~2 days after the 10-17 re-presentation. Recovery from
the fade, but short delay — long-delay retention on this node still unproven.

**Sharpening given (not a correction):** ordering is load-bearing — write the PENDING
receipt BEFORE the send; a receipt written after the crash is no receipt.

Still owed: lapsed three-outcome tail question (posed 10-18, unanswered); full
five-question audit re-ping ~2026-10-22..23.
