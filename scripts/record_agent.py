"""Record one consumer Agent run without importing the framework checkout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from agent_regression import record_run

from agent_order import OrderTools, build_agent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["normal", "wrong-resource", "skip-tool", "misread-result"], default="normal")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    trace = record_run(
        build_agent(args.variant),
        {"order_id": "123"},
        OrderTools(),
        run_id=f"consumer-order-{args.variant}",
        metadata={"consumer_repo": "agent-regression-pilot", "variant": args.variant},
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
