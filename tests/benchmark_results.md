# Benchmark: Kruskal vs Prim

- Command: `python tests/benchmark.py` (seed `20261025`, graph for size n uses seed `20261025 + n`)
- Inputs: random multigraphs (loops and parallel edges allowed), weights uniform in [-1e9, 1e9]
- Environment: Python 3.12.10, Windows 11, CPU AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD, 16 logical CPUs
- Timer: `time.perf_counter`; 1 warm-up call (not recorded) + 5 timed runs per method and size
- Boundary: only the algorithm call on a prepared request dict; JSON parsing, generation and
  output excluded; no compilation step in Python

| n | m | Kruskal runs (ms) | Kruskal median (ms) | Prim runs (ms) | Prim median (ms) | Prim / Kruskal | MST cost | components |
|---:|---:|---|---:|---|---:|---:|---:|---:|
| 1000 | 5000 | 3.0, 3.6, 4.6, 4.1, 3.7 | 3.7 | 9.9, 8.7, 10.6, 11.6, 10.6 | 10.6 | 2.84 | -762464259097 | 1 |
| 10000 | 50000 | 43.3, 60.7, 52.9, 43.7, 38.5 | 43.7 | 104.3, 127.5, 105.7, 99.2, 96.9 | 104.3 | 2.39 | -7617089237995 | 1 |
| 100000 | 250000 | 334.1, 329.0, 327.6, 374.6, 334.6 | 334.1 | 848.0, 832.7, 819.5, 837.2, 903.2 | 837.2 | 2.51 | -52717148650627 | 690 |
