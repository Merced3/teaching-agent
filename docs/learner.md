# Learner

Everything here is a **hypothesis about one specific mind**, to be confirmed or corrected by evidence. Nothing here is flattering filler. The learner may edit this file directly at any time — their edits outrank agent inference.

## Status key

- `confirmed` — learner said it directly, or observed repeatedly
- `observed` — seen in sessions, not yet deliberately tested
- `hypothesis` — agent guess; test before relying on it
- `outdated` / `contradicted` — kept visible, not deleted

## How this mind seems to learn

| claim | status | evidence |
| --- | --- | --- |
| Learns while doing other things; values audio/overview formats | confirmed | requested podcast-style lessons twice |
| Audio alone did not retain well | confirmed | learner's own report, 2026-08-26 |
| Tolerates long material if it builds from simple to professional | confirmed | requested exactly this shape |
| Wants systems that adapt to them rather than fixed curricula | confirmed | this project's founding requirement |
| Thinks in systems/architecture; comfortable with engineering metaphors | observed | frames learning problems as pipelines, ports, adapters |
| Prefers being shown assumptions explicitly and having them challenged | observed | asked the agent to "examine assumptions" |
| Needs struggle to stay in the material, logistics removed | hypothesis | consistent with requests; untested under real teaching |
| Retention strength unknown — no delayed-recall evidence exists yet | hypothesis | needs first retention check |
| Discord is the learner's home surface for agents | confirmed | stated 2026-08-26; runs socratic-partner there |
| Wants newly-learned knowledge actively stress-tested, incl. unprompted questions | confirmed | stated 2026-08-26 |
| Treats authorities/quotes as motivation, not evidence | confirmed | corrected DHH framing unprompted |
| Consistency over optimality: "suboptimal yet consistent beats optimal and not consistent" (gym analogy) | confirmed | stated 2026-08-26; system-level design constraint |
| Learning must fit around work/cleaning/exercise; dedicated desk time feels high-cost | confirmed | stated 2026-08-26; motivation for audio + async channels |
| Learns best when anchored to things he built himself | hypothesis | requested project-anchored teaching; untested until first loop |
| Loses the goal/thread in long sessions; needs periodic re-anchoring, not just session-start context | observed | first loop, 2026-08-26: forgot the loop's purpose mid-probe |
| Needs EXPLICIT verdicts — right/wrong per part, stated first — or the feedback loop isn't felt even when it exists | confirmed | stated 2026-10-04: "I haven't felt a feedback loop... respond with whether I got something wrong or the ways I got it correct"; verdict-card format adopted same day (decision-log 2026-10-04) |
| Frames learning as training ("bodybuilding of the mind"); wants visible progress metrics | confirmed | stated 2026-10-04; gym analogy recurs (cf. consistency-over-optimality, 2026-08-26) |
| Wants synchronous voice conversation as a modality (walk/sauna: interrupt, ask, debate) | confirmed | stated 2026-08-26; motivated by wanting to interrupt the passive audio lesson mid-listen |
| Software books go "in one ear and out the other" | confirmed | self-report 2026-08-26; corroborates H1 pattern beyond audio |
| Retention without retrieval practice is weak — first system measurement: 0/5 presented-only concepts survived 5 days unaided | observed | 2026-08-31 recall check; partial shapes retained (scope of crash window) but mechanisms lost; consistent with H1, n=1 |
| Short targeted lecture episodes + voluntary repetition (sauna listening) DO carry recall — learner credits them for unaided recall of invariant/write-boundary names (~3d) and crash-window general form (~4d), both previously serial faders | observed | self-report 2026-10-06; revises H1: long single-pass audio fails, short repeated episodes work, n=1; possibly the episodes functioned as compact re-presentations the learner chose to repeat — repetition was learner-driven, not scheduled |
| Self-corrects mid-answer and re-reads the actual question when confused ("wait what am I answering") — then answers the real one well | observed | 2026-08-31 node-1 session; confusion resolved by learner, not teacher |
| Generalizes taught concepts unprompted when they land (extended crash window → idempotency as result-invariant; inferred atomicity's role before node 2) | observed | 2026-08-31; suggests checks that require prediction (not just recall) fit this mind |
| Failed delayed recall even on a self-generated concept (asked "what does idempotency mean" ~1 day after coining its shape himself); re-derived instantly once re-presented | observed | 2026-09-01 node-2 session; strongest single data point yet for H5 (retrieval practice beats self-generation alone) |
| Treats "scenario has a bad outcome" as "my answer is wrong" — instinct is to fix everything; needs the reframe that every crash gap has a damage mode and design = choosing recoverable damage | observed | self-reported + observed in node-2 ordering check, 2026-09-01 |
| Asks to ground synthetic examples in the real codebase to avoid telephone-game drift across sessions | observed | 2026-09-01: requested repo verification before closing node 2; aligns with H8 (project-anchored teaching) |
| Hits a fatigue wall where reasoning stops mid-session and says so plainly ("Im pretty spent", "my thinking has stopped"); wants to interrupt long explanations as they happen | observed | 2026-09-01 node-2 re-test: proof chain stopped clicking under stacked questions; one diagram + one sentence landed where paragraphs didn't; corroborates the confirmed want for synchronous voice modality (interrupt-as-you-go) |
| Diagram-first recovery: when verbal chains stop landing, a single boxed picture of the full flow re-anchors immediately | observed | 2026-09-01: envelope diagram unlocked the charge-transaction framing after text-only corrections failed |
| Voice modality requirement: responses must be short by default — long answers/explanations exceed what he can track aurally, and asking the agent to repeat is costly; the learner will explicitly say when to "go into detail" | confirmed | stated 2026-09-01 as a hard requirement for the future voice/conversational modality (walk/sauna interrupt-style); evidence of working state: this session's fatigue wall under stacked paragraphs |
| Self-diagnosed outsourcing the question-generation to the teacher: was waiting for the teacher to ask the questions he wanted asked instead of asking them himself; resolved to ask directly when unclear | observed | self-reported 2026-09-01 after the node-2 re-test; teacher should prompt "what question do you wish I'd asked?" when confusion lingers |
| Dense questions cause first-read blanking; learner re-reads and self-recovers, and asks for lead-with-the-plain-version ("state whatever the user is trying to learn as SIMPLY as possible") | confirmed | self-reported + observed 2026-09-03 node-3 session: floundered on multi-clause lock-in question, recovered fully after plain one-sentence restatement; teacher rule: introduce at most one new word per sentence |
| Self-flags wrong-layer answers unprompted ("Am I answering the wrong layer again?") | observed | 2026-09-03: the 2026-08-26 one-layer-up probe pattern is becoming a self-correcting habit |
| Honest confidence calibration: reports "still not confident" right after a correct first-transfer | observed | 2026-09-03 wallet transfer; treat as first-landing signal, not as failure — but do re-check with delay |
| Text ambiguity causes real misreads; learner hypothesizes voice (Discord call / audio) would disambiguate via prosody/tone and slow-broken phrasing ("slowing down words when they need to be") | observed | self-reported 2026-09-03 after misreading teacher's describing-vs-prescribing recap; reinforces the confirmed voice-modality want and the plain-form-first preference |

| Manipulated mechanisms stick, names/lookup details evaporate: at 13 days, race mechanism re-derivable and atomicity recalled unaided, but invariant/enforcement names, keyed-receipt, and rowcount detail were gone | observed | 2026-09-16 recall checks; suggests reps should target names+details, not re-teach mechanisms |
| Distrusts stale state after a break and asks for re-measurement; set standing rule that agent must check the real date when he says "it's been a while" | confirmed | 2026-09-16 session start; rule recorded in session-handoff.md |
| Self-correction habit now operates on NEW material, not just recall: talked himself out of his own Discord-receipt proposal mid-answer, deriving the unweldable-outside-world insight unaided | observed | 2026-09-18 node-5 lock-in ("OHHH wait... nvm my b") |
| Over-reaches for one-shot complete answers under load, then self-trims when reminded to answer only the question asked | observed | 2026-09-18 node-5 ("Im trying to one shot the whole Entire process") |
| When a name's meaning is fuzzy, re-anchors on the machinery instead of the word (enforcement → WHERE+rowcount) | observed | 2026-09-18 recall checks; names still need targeted production reps |
| Irritated by preemptive constraint-framing ("what it's NOT", guardrails) in plans — wants foundational generalization that keeps future paths open; present designs as capabilities, not exclusions | confirmed | stated 2026-09-18 re: rep-runner plan ("Don't try and 'not' build anything... giving us guard rails irritates me") |
| Enjoys open-ended "you lead me" drill reps — free-form back-and-forth on a scenario, no scaffold, sustained voluntarily across ~10 turns | observed | 2026-10-06 voice session: requested "reps of software dev stuff, let's just go back and forth, you lead me"; stayed engaged through corrections, said honest "I don't know" when stretched, ended on own terms |
| Derives the target mechanism unaided when probed from a scenario, needing only the NAME handed over — replicated twice in one session: invented the precondition (write receipt before external call, chose prefer-loss himself) and independently proposed the reconciliation job as an async background process | observed | 2026-10-07 preconditions lesson; strengthens the 2026-09-18 self-correction/derivation pattern — Socratic probing gets mechanisms for free; reps should spend on names (precondition, reconciliation) since names are what fade |
| Deliberately repeats names aloud to memorize them and asks for mnemonics when a name keeps fading — self-directed name-retention tactics appearing spontaneously | observed | 2026-10-08 voice session: repeated 'reconciliation job' aloud several times ('I'm only repeating it to kind of stick it in my head'), then asked 'what would be an easy way for you to recommend me to remember it?'; supply mnemonics for fading names on request |
| Transfers freshly-taught mechanisms to a new problem within ~1 day without prompting: aimed the keyed receipt cold at the unknown-state-after-timeout scenario, including the confirm-before-retry shape | observed | 2026-10-08 timeout lesson opening; consistent with the 2026-08-31 unprompted-generalization pattern — transfer instincts are strong, lookup details are what need reps |
| Strong-transfer instinct's shadow side: reaches for the MOST RECENT mechanism even when it solves a different problem — aimed the keyed receipt at the thundering-herd load problem | observed | 2026-10-08 backoff lesson; one aim-correction sufficed and he then derived the herd crash unaided — probe 'which problem does this solve?' when he grabs a shiny recent tool |
| Requests ongoing spaced re-testing of material he predicts he will forget, per-topic and unprompted ('I would keep testing me on those 5 questions... I feel like I'm going to forget them soon too') — retention self-management is now proactive, not just reactive | confirmed | stated 2026-10-16 after the audit re-ping; extends the 2026-08-26 standing want for unprompted stress-testing into self-directed per-topic scheduling |
| Self-initiates the harder test question to check his own understanding ("I'm gonna try and push on why both may be needed just to see if I understand it correct") — treats the lesson as something to stress-test himself against, not just receive | observed | 2026-10-09 backoff/jitter voice lesson; consistent with the 2026-10-06 self-requested drill reps and the 2026-10-03 'did I get those right' — let him attempt first when he volunteers, correct plainly |

| Forgets lesson-lifecycle command syntax between lessons; stating the exact command (`/lesson end`) in the wrap-up message is what lets him close cleanly — worth doing every time | observed | self-reported 2026-10-21 timeout lesson: 'I kind of forgot about it and was wondering how to end it'; asked that this be recorded for future sessions |
| Cost-aware about autonomous model spend: challenged a $2 session-cost warning after ~14 messages and asked whether the accounting was correct; accepted the answer when it was traced to pi's own reported stats. Levers offered (shorter sessions, trim current-state.md, fewer pings, cheaper ping model) left open | observed | 2026-10-19; watch whether cost concern changes his tolerance for unprompted pings (H5's learner-tolerance experiment) |

## Preferences to respect now

- Plain language first, professional depth by the end.
- Call out uncertainty and unverified sources plainly.
- Don't overfit structure early; keep the system fluid.
- Private by default.

## Open questions for the learner (fill in over time)

- Best session length before fatigue?
- Morning/evening? Multitasking vs. focused?
- Quiz tolerance: do checks feel useful or annoying?
- What does "up to speed" feel like to you — being able to *do*, or to *converse about*?
- Do silent prediction pauses in audio actually trigger retrieval attempts for you, or do you tune them out?
| Audio re-listening produces recognition fluency, which he initially reads as retention ("it will get better the more I listen") — needs the recall-gate reminder at those moments | observed | 2026-09-03 post-sauna/car report; recalled the node-2 lock-in phrase (prior teaching) but attributed improvement to re-listening |
| Works well in text lessons too — first text-mode lesson (2026-10-09 timeout tail) after a voice-only stretch; produced a careful written restatement voluntarily ("took me like 15mins to write this") and caught his own error on one prompt. Text gives him time to compose; keep both modalities live | observed | 2026-10-09 |
| Answers roughly ONE ping question per day; same-day repeat pings and re-asks get no response, next-day single questions get answered. Multi-part questions get partially answered (answers the half that landed), then completed willingly when the remainder is re-asked plainly ('apologies, I forgot you were asking 2 questions'). One outstanding question at a time is the right ping cadence | observed | 2026-10-10..13 cold-ping stretch: 10-10 answered same day, 10-11 question answered 10-12 after one re-ask, two same-day SILENT slots while a question was fresh; 10-13 two-part question half-answered then completed on plain re-ask; corroborated 2026-10-18..19 — 10-18 question unanswered (two later same-day slots SILENT), 10-19 single question answered |
| Compound ping questions confuse him — flagged one himself ('the question was confusing... didn't exactly know what I was answering'); a clean single-action re-ask ('walk me through what your code does, step by step') produced a full unaided production rep hours later | observed | 2026-10-20 receipt-retry re-verification; extends the one-question-at-a-time finding from multi-PART to multi-CLAUSE questions — ask one plain thing |
| Name-retention window measurable per-name: the state-machine name holds unaided at ~2 days (10-17) but is gone at ~3–5 (faded 10-15, faded again 10-20 'I do not know' ~3d after the win); recognition on re-presentation stays intact ('oh it was that') — name production reps should land inside ~48h of a win | observed | 2026-10-20; same shape as the invariant/enforcement name pattern (10-15..16) |
| Chronic-fading lookup details respond better to PRODUCTION reps than verbal re-explanation: the receipt-retry move faded ~6x under verbal ping/re-presentation (including a same-morning re-presentation), then came out unaided in hand-written pseudocode the same day | observed | 2026-10-20; caveat — production was same-day as re-presentation, retention still unproven, cold re-probe owed; consistent with 10-03 where the production rep passed cold at ~2 weeks |
| Pseudocode syntax is a noise layer over his actual design knowledge: his 10-23 written rep scored a fade on retry-path semantics, but one plain prompt surfaced the fully correct intent ('skips to checking the result'); he says himself 'I'm bad at writing pseudocode'. Ask for plain-English walkthroughs, not code, when probing design recall | observed | 2026-10-23 receipt-retry production rep; logged as rep-form change in decision-log 2026-10-23 |
