# Agent Regression Pilot

This is an independent consumer repository for [Agent Regression Kit](https://github.com/ANTAO94/agent-regression-kit).
It owns a small two-tool order Agent and consumes only the published v4.23.0
wheel. It does not import the kit source tree, use `PYTHONPATH` to the producer
repository, or copy its implementation.

## What this proves

The consumer Agent looks up an order, uses the returned customer ID to check a
balance, and emits structured claims. The Contract checks:

- the order resource ID and required tool calls;
- that the dependent balance lookup uses the customer returned by the first tool;
- the final structured order status and `balance_verified` claim;
- the absence of an unauthorized refund tool and the two-step limit.

The CI workflow injects three independent regressions and requires each one to
return exit code 1:

| Injected change | Expected blocking evidence |
| --- | --- |
| Query order `999` instead of `123` | required tool/argument and error/path differences |
| Skip `get_balance` | missing required tool, claim and relation evidence |
| Report `shipped` although the tool returned `not_shipped` | Contract assertion and result-interpretation differences |

This is consumer-side evidence, not a claim that every external Agent can be
auto-instrumented. The Agent and its tool double are deliberately readable so
the boundary between application code and the released regression kit is clear.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-ci.txt

PYTHONPATH=. python scripts/record_agent.py --variant normal --out work/candidate.trace.json
agent-regression check --config contracts/order-status.json
agent-regression compare --config contracts/order-status.json
```

The normal comparison exits 0. To see the gate catch a real regression:

```bash
PYTHONPATH=. python scripts/record_agent.py --variant misread-result --out work/candidate.trace.json
agent-regression compare --config contracts/order-status.json
echo $?  # 1
```

For the other negative cases, use `wrong-resource` or `skip-tool` as the
`--variant`. Reports are written under `work/reports/`; the reviewed baseline
is `baselines/order-status.trace.json` and is never overwritten by CI.

## Version and evidence boundary

The exact release wheel URL and SHA-256 are recorded in
[`requirements-ci.txt`](requirements-ci.txt) and
[`upstream.lock.json`](upstream.lock.json). Upgrade the wheel and update its
hash in a reviewed change; do not install from the producer working tree.

The v4.23 consumer check is intentionally narrow: it proves that a separately
maintained Agent can install the released wheel and that the public recording,
Contract, comparison and exit-code boundaries still catch three application
regressions. It does not claim that this one Agent represents every framework
or production workload.
