"""Create a small v4.31 sampling-study bundle from the consumer baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_regression import ComparisonPolicy, ContractPolicy, canonical_sha256, sha256_file


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_trace(source: Path, destination: Path, run_id: str) -> None:
    trace = json.loads(source.read_text(encoding="utf-8"))
    trace["run_id"] = run_id
    write_json(destination, trace)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    output = args.out_dir.expanduser().resolve()
    source = ROOT / "baselines/order-status.trace.json"
    baseline = output / "baseline.trace.json"
    write_trace(source, baseline, "consumer-study-baseline")

    input_object = {"order_id": "123"}
    tool_schema = {"tools": ["get_order", "get_balance"], "protocol": "consumer-fixture"}
    input_sha256 = canonical_sha256(input_object)
    tool_schema_sha256 = canonical_sha256(tool_schema)
    evidence_files = {
        "input": output / "evidence/input.json",
        "tool_schema": output / "evidence/tool-schema.json",
        "adapter": output / "evidence/adapter.json",
    }
    write_json(evidence_files["input"], {"input_sha256": input_sha256})
    write_json(evidence_files["tool_schema"], {"tool_schema_sha256": tool_schema_sha256})
    write_json(evidence_files["adapter"], {"name": "independent-order-agent", "version": "0.1.0"})

    contract = json.loads((ROOT / "contracts/order-status.json").read_text(encoding="utf-8"))["contract"]
    comparison_policy = {"final_answer_mode": "claims-only", "contract": contract}
    normalized_policy = ComparisonPolicy(
        final_answer_mode="claims-only",
        contract=ContractPolicy.from_dict(contract),
    )
    runs = []
    for ordinal in (1, 2):
        run_id = f"consumer-study-{ordinal}"
        path = output / f"runs/run-{ordinal}.trace.json"
        write_trace(source, path, run_id)
        runs.append({"id": run_id, "trace": str(path.relative_to(output)), "sha256": sha256_file(path)})

    manifest = {
        "schema_version": "0.1",
        "study_id": "consumer-order-study",
        "baseline": str(baseline.relative_to(output)),
        "runs": runs,
        "provenance": {
            "provider": "consumer-fixture",
            "model": "independent-order-agent-v0.1",
            "adapter": "consumer-fixture",
            "study_id": "consumer-order-study",
            "input_sha256": input_sha256,
            "tool_schema_sha256": tool_schema_sha256,
            "dataset_revision": "consumer-fixture-v1",
            "parameters": {"temperature": 0.0},
        },
        "comparison_policy": comparison_policy,
        "policy": {"min_runs": 2},
        "evidence": [
            {
                "id": f"{role}-evidence",
                "role": role,
                "path": str(path.relative_to(output)),
                "sha256": sha256_file(path),
            }
            for role, path in evidence_files.items()
        ],
        "integrity": {
            "require_trace_hashes": True,
            "require_evidence_index": True,
            "required_evidence_roles": ["adapter", "input", "tool_schema"],
            "baseline_sha256": sha256_file(baseline),
            "comparison_policy_sha256": canonical_sha256(normalized_policy.to_dict()),
        },
    }
    manifest_path = output / "study.json"
    write_json(manifest_path, manifest)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
