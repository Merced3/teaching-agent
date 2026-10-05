# Crash Windows: The General Form

You already know this idea cold, so today is about sharpening it — pushing it from "a thing you recognize" into "a lens you can aim at any system, including ones nobody taught you about."

## The form, stated once, generally

A crash window is the stretch of execution between two durable steps. Not between two objects, not between two function calls — between two points where something becomes permanent. Before the first durable step, a crash costs you nothing: nothing was recorded, nothing happened, you just start over. After the second durable step, a crash also costs you nothing: the whole unit of work is safely on record. It is only inside the window — after durability step one, before durability step two — that a crash leaves the world in a state that half-happened. The first step is recorded forever; the second never arrives. That half-state is the whole problem. Everything else is commentary.

## Why "two durable steps" and not "two writes"

Notice the word is steps, not writes, and durable is doing the real work. A log line to a file that might be buffered and lost is not a durable step. An in-memory flag is not a durable step. A durable step is one that survives the process dying at the worst possible instant. When you audit a system for crash windows, the first question is never "what does this code do" — it is "where, exactly, does this system cross from forgettable to permanent?" Mark those crossings, and the windows draw themselves between consecutive ones.

## The choice the window forces on you

Here is the part that generalizes furthest: every crash window is a forced choice between duplication and loss. If the first durable step is the one the outside world can see — the charge, the email, the deployed artifact — then a crash inside the window means you can't know whether it happened, and retrying risks doing it twice. Duplication risk. If the first durable step is your own internal record and the externally visible effect comes second, then a crash inside the window means the effect never happened, and you know that for certain — so you can safely retry, at the cost of maybe losing work you must redo. Loss risk. There is no arrangement with zero risk. There are only arrangements where you have chosen which failure you're willing to have. Mature engineers are not people who eliminate crash windows. They are people who can look at any pipeline, find the windows, and say out loud which side of the choice each one sits on — and whether that's the right side.

## Your own proof: the LLM call

You did this already, unprompted, on socratic-partner. Around the LLM call you chose loss over duplication — you reasoned that the first durable step sits after the call, so a crash mid-call leaves nothing recorded, the turn simply never happened, and the user retries. No double-charge of anyone's trust, no phantom half-responses. That reasoning is the general form working. You didn't recall a rule; you aimed the lens at new material and it resolved.

## Two drills for aiming the lens at strangers

First drill: take any system you use daily — your CI pipeline, your bank app, your Discord hub's message flow — and ask only one question: where does it cross from forgettable to permanent? You will usually find the crossings are fewer and further apart than the code suggests, which means the windows are bigger than anyone intended.

Second drill: for each window you find, don't fix anything. Just name the choice. Crash here means duplicate, or crash here means lose? If you can't tell which, that is the finding — an unexamined window is a window where the choice was made by accident.

## One sentence to keep

A crash window is the space between two durable steps; it cannot be removed, only moved — and moving it means choosing duplication or loss on purpose instead of by accident.
