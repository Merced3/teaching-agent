# The keyed-receipt trick: why a retry must return the recorded success

You already know the shape of this one cold. Check for the ID. If it's there, skip. If it's not, do the action and write a record. That part has stuck — you've reproduced it unaided, weeks later, more than once.

So this episode is not about the shape. It's about the piece that keeps slipping away: what the receipt is for, and why the retry has to hand back the recorded success instead of skipping, failing, or retrying blind.

Here's the scenario that makes it click. Imagine you're the caller. You ask a handler to charge a customer forty dollars, tagged with request ID seven. The handler does the work — the charge goes through — and then, before it can tell you, something crashes. Network drop, timeout, process restart, doesn't matter. What you see is: no answer.

Now you're stuck in the worst spot in distributed systems. Did it work? You don't know. If you send the request again and the handler blindly redoes the work, the customer pays twice. If you never retry, maybe the customer never paid at all. Both are bad, and you can't tell which world you're in.

The keyed receipt exists to answer one question, later: what happened last time? Not "did I see this ID before" — that's the half-answer that keeps fading. The receipt stores the outcome. The charge succeeded, here's the confirmation, here's the amount, here's the result you would have gotten if nothing had crashed.

So when the retry arrives with ID seven, the handler looks up the receipt, finds it, and here's the whole point: it replies with that recorded result. Success. Same answer the first attempt would have given. From the caller's seat, it's as if the crash never happened. The retry isn't a skipped action — it's a recovered answer.

Now you can see why the two tempting alternatives both break the trick.

First alternative: the retry skips and says nothing, or just says "already handled." Sounds efficient. But the caller never learns the result. It retried precisely because it didn't know what happened — and it still doesn't. You deduplicated the work and lost the information. That's the version you drifted toward before: dedup that swallows the outcome. It's a lock with no keyhole.

Second alternative: the retry fails loudly — "duplicate request, error." Now the caller knows something happened, but not whether it was the thing it wanted. Was the charge completed before the error, or is this a refusal? Ambiguity again. An error is not an answer.

Only the recorded success closes the loop. Retry comes in, receipt comes out, caller walks away knowing exactly what state the world is in. That's what upgrades a harmless retry into a safe retry — and remember the distinction from node five: idempotency is a property of the effect, retry-safety is a property of the caller. The receipt is the bridge. It lets the caller retry blindly and still learn the result.

One more sharpening, because you caught this yourself last time: the receipt stores the result, not just the ID. A bare ID tells you "this ran." The full receipt tells you "this is what running it produced." The difference is the difference between a stub and an answer.

And the placement detail, which you also already own: the receipt lives in your own durable store, written atomically with the send attempt — not at the provider. The provider's side is the unweldable outside world; you can't make it transactional. Your store, you can. So the write of the effect and the write of the receipt succeed or fail together, and there's no window where the charge exists but the receipt doesn't.

Let's compress it into one line you can keep: the receipt is not a dedup flag — it's the answer, saved. A retry doesn't skip the work. A retry retrieves the answer the crash stole from you.

If you want to test yourself on this later, here's the cold rep: write the handler pseudocode from nothing. Check the store for the ID. Absent — do the action, write the receipt with the result, atomically, return the result. Present — read the receipt, return the recorded result. That's the whole trick, and now the why behind every line of it should be load-bearing, not memorized.
