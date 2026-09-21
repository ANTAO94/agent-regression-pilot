"""Create a consumer-side readiness manifest with an explicit pending gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    output = args.out_dir.expanduser().resolve()
    lock = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
    evidence = output / "evidence/released-wheel.json"
    write_json(evidence, lock["agent_regression_kit"])

    manifest = {
        "schema_version": "0.1",
        "profile": "final-v4",
        "target_version": lock["agent_regression_kit"]["version"],
        "checks": [
            {
                "id": "released-wheel-lock",
                "kind": "evidence",
                "files": [{"path": str(evidence.relative_to(output)), "sha256": sha256(evidence)}],
            },
            {
                "id": "independent-user-study",
                "kind": "external",
                "status": "pending",
                "reason": "the consumer does not fabricate an independent participant record",
                "evidence": [],
            },
        ],
    }
    manifest_path = output / "readiness.json"
    write_json(manifest_path, manifest)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
