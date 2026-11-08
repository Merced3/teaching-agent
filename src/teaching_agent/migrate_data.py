"""Read-only source copy: operational JSON → teaching DB, generated audio → R2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import boto3

from .storage import PostgresStateStore

_JSON_FILES = ("pings.json", "lesson-state.json", "session-registry.json")


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def copy_operational_json(source_dir: Path, database_url: str) -> dict:
    store = PostgresStateStore(database_url)
    report = {"source": str(source_dir), "documents": {}}
    sources = {}
    for name in _JSON_FILES:
        path = source_dir / name
        if not path.is_file():
            report["documents"][name] = {"source": "absent"}
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        key = path.stem
        if store.load(key) is not None:
            raise ValueError(f"destination operational_state key is not empty: {key}")
        sources[name] = (key, payload)
        report["documents"][name] = {
            "source_bytes": path.stat().st_size,
            "source_records": len(payload) if isinstance(payload, list) else 1,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "payload_sha256": _digest(payload),
        }
    for name, (key, payload) in sources.items():
        store.save(key, payload)
        copied = store.load(key)
        if copied != payload or _digest(copied) != _digest(payload):
            raise ValueError(f"operational JSON verification failed: {name}")
        report["documents"][name]["destination_verified"] = True
    return report


def copy_generated_assets(source_root: Path) -> dict:
    required = (
        "TEACHING_AGENT_R2_ACCOUNT_ID", "TEACHING_AGENT_R2_ACCESS_KEY_ID",
        "TEACHING_AGENT_R2_SECRET_ACCESS_KEY", "TEACHING_AGENT_R2_BUCKET",
        "TEACHING_AGENT_R2_ENDPOINT",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError(f"missing R2 environment values: {', '.join(missing)}")
    client = boto3.client(
        "s3", endpoint_url=os.environ["TEACHING_AGENT_R2_ENDPOINT"],
        aws_access_key_id=os.environ["TEACHING_AGENT_R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["TEACHING_AGENT_R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    bucket = os.environ["TEACHING_AGENT_R2_BUCKET"]
    report = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".mp3", ".pcm"}:
            continue
        relative = path.relative_to(source_root).as_posix()
        key = (
            f"lectures/{relative.removeprefix('lessons/')}"
            if relative.startswith("lessons/")
            else relative if relative.startswith("out/") else f"out/{relative}"
        )
        client.upload_file(str(path), bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})
        head = client.head_object(Bucket=bucket, Key=key)
        body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        if body != path.read_bytes() or head["ContentLength"] != path.stat().st_size:
            raise ValueError(f"R2 verification failed: {relative}")
        report.append({
            "source": relative, "key": key, "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(), "verified": True,
        })
    return {"bucket": bucket, "objects": report, "count": len(report)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--assets-root", type=Path)
    args = parser.parse_args(argv)
    if not args.data_dir and not args.assets_root:
        parser.error("choose --data-dir and/or --assets-root")
    report = {}
    if args.data_dir:
        url = os.environ.get("TEACHING_AGENT_DATABASE_URL", "").strip()
        if not url:
            parser.error("TEACHING_AGENT_DATABASE_URL is required")
        report["operational"] = copy_operational_json(args.data_dir, url)
    if args.assets_root:
        report["assets"] = copy_generated_assets(args.assets_root)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
