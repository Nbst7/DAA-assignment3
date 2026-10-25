# Own tests

Run everything from the repository root.

| Command | What it does |
|---|---|
| `python -m unittest discover -s tests -v` | All own tests (about 5 s): hand cases, random cross-checks, deep chains, full limits, route helper, state reset |
| `python tests/write_cases.py` | Rewrites `my_cases.jsonl`, `my_cases_actual.jsonl` and `CASES.md` (inputs, justified expected answers, actual outputs) |
| `python tools/run.py --input tests/my_cases.jsonl` | Prints the launcher's actual results for the hand cases |
| `python tools/run.py --check` | The 36 public cases (pass/fail only) |
| `python tests/benchmark.py` | Kruskal vs Prim benchmark, writes `tests/benchmark_results.md` |

Files: `my_cases.py` (cases with justification), `oracles.py` (independent brute-force, Floyd, Tarjan, Kahn
oracles and validators, never imports `algorithms.py`), `test_algorithms.py`, `write_cases.py`, `benchmark.py`.

Non-unique answers (MST edge sets, topological orders, SCC labels, DAG parent edges) are checked by validity.
`HandCases.test_alternative_valid_answers_are_accepted` shows alternative valid answers and
`HandCases.test_invalid_witnesses_are_rejected` shows invalid witnesses being rejected.
