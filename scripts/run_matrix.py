"""Record the consumer-owned ten-case order Agent matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_regression import record_run

from agent_order import OrderTools, build_matrix_agent


ROOT = Path(__file__).resolve().parents[1]


def load_cases() -> list[dict[str, object]]:
    value = json.loads((ROOT / "matrix/cases.json").read_text(encoding="utf-8"))
    if not isinstance(value, list) or len(value) != 10:
        raise ValueError("matrix/cases.json must contain exactly ten cases")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--mutation",
        choices=["none", "wrong-resource", "skip-tool", "misread-result"],
        default="none",
    )
    parser.add_argument("--mutation-case")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    cases = load_cases()
    for case in cases:
        case_id = str(case["id"])
        output = args.out_dir / f"{case_id}.trace.json"
        if output.exists() and not args.force:
            raise SystemExit(f"refusing to overwrite existing baseline: {output}")
        request = {
            "case_id": case_id,
            "order_id": case["order_id"],
            "style": case["style"],
        }
        trace = record_run(
            build_matrix_agent(
                mutation=args.mutation,
                mutation_case=args.mutation_case,
            ),
            request,
            OrderTools(),
            run_id=f"consumer-matrix-{case_id.replace('/', '-')}",
            metadata={
                "consumer_repo": "agent-regression-pilot",
                "matrix_case": case_id,
                "mutation": args.mutation if args.mutation_case in {None, case_id} else "none",
            },
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"recorded {len(cases)} cases in {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
