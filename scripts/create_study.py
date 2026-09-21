"""Create a small sampling-study bundle from the consumer baseline."""

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
        "provider_output": output / "evidence/provider.json",
        "model_output": output / "evidence/model.json",
        "dataset": output / "evidence/dataset.json",
    }
    write_json(evidence_files["input"], {"input_sha256": input_sha256})
    write_json(evidence_files["tool_schema"], {"tool_schema_sha256": tool_schema_sha256})
    write_json(evidence_files["adapter"], {"adapter": "consumer-fixture", "version": "0.1.0"})
    write_json(evidence_files["provider_output"], {"provider": "consumer-fixture"})
    write_json(evidence_files["model_output"], {"model": "independent-order-agent-v0.1"})
    write_json(evidence_files["dataset"], {"dataset_revision": "consumer-fixture-v1"})

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
                "role": "provider_output" if role == "model_output" else role,
                "path": str(path.relative_to(output)),
                "sha256": sha256_file(path),
            }
            for role, path in evidence_files.items()
        ],
        "evidence_bindings": [
            {
                "evidence_id": "input-evidence",
                "target": "provenance.input_sha256",
                "field": "input_sha256",
            },
            {
                "evidence_id": "tool_schema-evidence",
                "target": "provenance.tool_schema_sha256",
                "field": "tool_schema_sha256",
            },
            {
                "evidence_id": "adapter-evidence",
                "target": "provenance.adapter",
                "field": "adapter",
            },
            {
                "evidence_id": "provider_output-evidence",
                "target": "provenance.provider",
                "field": "provider",
            },
            {
                "evidence_id": "model_output-evidence",
                "target": "provenance.model",
                "field": "model",
            },
            {
                "evidence_id": "dataset-evidence",
                "target": "provenance.dataset_revision",
                "field": "dataset_revision",
            },
        ],
        "integrity": {
            "require_trace_hashes": True,
            "require_evidence_index": True,
            "required_evidence_roles": [
                "adapter",
                "dataset",
                "input",
                "provider_output",
                "tool_schema",
            ],
            "require_evidence_bindings": True,
            "required_evidence_bindings": [
                "provenance.adapter",
                "provenance.dataset_revision",
                "provenance.input_sha256",
                "provenance.model",
                "provenance.provider",
                "provenance.tool_schema_sha256",
            ],
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
