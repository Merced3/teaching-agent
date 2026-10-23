"""Knowledge log (design approved 2026-10-21, build is session #6):
append-only JSONL evidence events as the source of truth; everything else
(current-state view, owed pings, internal scheduling fields) derived and
regenerable.

Black-box, behavior-level: these tests drive the CLI boundary
(scripts/kb_append.py, scripts/kb_derive.py, scripts/kb_migrate.py) as
subprocesses against a temp kb/ directory — never internals.

NOTHING IS IMPLEMENTED YET. Every test here is expected to fail until
session #6 lands the build; they are committed xfail so CI stays green.
See docs/proposals/knowledge-storage.md, "Adopted design (2026-10-21)".
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
APPEND = REPO / "scripts" / "kb_append.py"
DERIVE = REPO / "scripts" / "kb_derive.py"
MIGRATE = REPO / "scripts" / "kb_migrate.py"

XFAIL_REASON = "knowledge log not built yet (design approved 2026-10-21; build is session #6)"
pytestmark = pytest.mark.xfail(reason=XFAIL_REASON, strict=False)


def run_cli(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def append(kb: Path, event: dict) -> subprocess.CompletedProcess[str]:
    return run_cli(APPEND, "--kb", str(kb), "append", "--event", json.dumps(event))


def evidence_event(node: str, level: str, **overrides) -> dict:
    event = {
        "type": "evidence",
        "ts": "2026-10-21T12:00:00Z",
        "node": node,
        "level": level,
        "delay_days": 0,
        "coached": False,
        "channel": "discord-text",
        "session": "sessions/test.md",
        "notes": "",
    }
    event.update(overrides)
    return event


# 1. Append-only is enforced: history is never rewritten, and the append CLI
#    (the ONLY write path) refuses to write onto a tampered log.
def test_append_only_enforced(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    assert append(kb, evidence_event("sd/atomicity", "recalled", delay_days=6)).returncode == 0
    assert append(kb, evidence_event("sd/atomicity", "recalled", delay_days=14)).returncode == 0

    log = kb / "events.jsonl"
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    # Attacker/bug rewrites history: downgrade the first event in place.
    tampered = json.loads(lines[0])
    tampered["level"] = "presented"
    log.write_text(
        json.dumps(tampered) + "\n" + lines[1] + "\n", encoding="utf-8"
    )

    # The next append must fail — the write boundary detects the broken chain.
    result = append(kb, evidence_event("sd/atomicity", "applied", delay_days=20))
    assert result.returncode != 0
    # And the log must be untouched by the refused write.
    assert len(log.read_text(encoding="utf-8").splitlines()) == 2


# 2. Derived current-state regenerates identically from the log: same log in,
#    byte-identical view out, even after the derived artifact is deleted.
def test_derived_current_state_regenerates_identically(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    append(kb, {"type": "node_created", "ts": "2026-10-20T09:00:00Z", "node": "sd/state-machine",
                "statement": "one named state at a time, moves on defined events", "edges": []})
    append(kb, evidence_event("sd/state-machine", "recalled", delay_days=2))
    append(kb, evidence_event("sd/state-machine", "recognized", delay_days=5, coached=True))

    first = run_cli(DERIVE, "--kb", str(kb), "current-state")
    assert first.returncode == 0

    # Derived artifacts are disposable: delete and rebuild.
    derived = kb / "derived"
    if derived.exists():
        for p in derived.iterdir():
            p.unlink()
    second = run_cli(DERIVE, "--kb", str(kb), "current-state")
    assert second.returncode == 0
    assert second.stdout == first.stdout
    assert "sd/state-machine" in first.stdout


# 3. An evidence level is never upgraded past its evidence: a presented-only
#    node is not "known", a coached answer is not unaided recall, and a
#    retention claim requires real delay.
def test_level_never_upgraded_past_evidence(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    append(kb, evidence_event("sd/backoff", "presented"))
    append(kb, evidence_event("sd/receipt", "applied", coached=True, delay_days=0))
    append(kb, evidence_event("sd/invariant", "recalled", delay_days=0))

    result = run_cli(DERIVE, "--kb", str(kb), "grades")
    assert result.returncode == 0
    grades = json.loads(result.stdout)

    assert grades["sd/backoff"]["level"] == "presented"
    # Coached production is evidence, but not an unaided claim.
    assert grades["sd/receipt"]["coached"] is True
    assert grades["sd/receipt"].get("unaided_level") is None
    # Zero-day recall is same-session evidence, NOT a retention win.
    assert grades["sd/invariant"]["level"] == "recalled"
    assert grades["sd/invariant"]["retention"] is not True


# 4. A migrated sample round-trips: prose from the "Prior:" chain becomes
#    events, and the derived view shows the grade the prose claimed. Lossy
#    spots are flagged, never guessed.
MIGRATION_SAMPLE = """\
Prior: 2026-10-14 (rule-2 re-verification ping: node 2 transactions — \
ATOMICITY recalled unaided ~6 WEEKS after last evidence: 'written as one \
executable, either both make it through or nothing'. RETENTION WIN.)
Prior: [UNPARSEABLE GIBBERISH LINE WITH NO DATE OR NODE]
"""


def test_migrated_sample_round_trips(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    src = tmp_path / "sample-prior-chain.md"
    src.write_text(MIGRATION_SAMPLE, encoding="utf-8")

    result = run_cli(MIGRATE, "--kb", str(kb), "--source", str(src))
    assert result.returncode == 0

    events = [
        json.loads(line)
        for line in (kb / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    atomicity = [
        e
        for e in events
        if e.get("type") == "evidence" and "atomic" in e.get("node", "").lower()
    ]
    assert len(atomicity) == 1
    event = atomicity[0]
    assert event["level"] == "recalled"
    assert event["coached"] is False
    assert event["delay_days"] >= 40  # "~6 WEEKS" — delay is a dimension, not a level

    # The gibberish line was flagged, not guessed into an event.
    flags = [e for e in events if e.get("type") == "migration_flag"]
    assert len(flags) == 1
    assert flags[0].get("unverified") is True

    # And the derived view agrees with the prose's claim.
    grades = json.loads(run_cli(DERIVE, "--kb", str(kb), "grades").stdout)
    node = next(g for g in grades if "atomic" in g.lower())
    assert grades[node]["level"] == "recalled"
    assert grades[node]["retention"] is True
