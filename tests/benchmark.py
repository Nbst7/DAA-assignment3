"""Kruskal vs Prim benchmark. Run from the repository root:  python tests/benchmark.py

Timing boundary: only the call algorithms.kruskal(request) / algorithms.prim(request) on an
already built request dict (JSON parsing, graph generation, printing and process start-up are
excluded). Timer: time.perf_counter. One untimed warm-up call per method and size, then 5 timed
runs; the median is reported. Python needs no compilation. Results go to tests/benchmark_results.md.
"""

import os
import platform
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src", "Python"))

import algorithms as A  # noqa: E402

SEED = 20261025
RUNS = 5
SIZES = [(1000, 5000), (10000, 50000), (100000, 250000)]    # (n, m)
W = 10 ** 9


def make_graph(n, m, seed):
    rng = random.Random(seed)
    return [[rng.randrange(n), rng.randrange(n), rng.randint(-W, W)] for _ in range(m)]


def timed(func, request):
    start = time.perf_counter()
    result = func(request)
    return time.perf_counter() - start, result


def cpu_name():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def main():
    rows = []
    for n, m in SIZES:
        edges = make_graph(n, m, SEED + n)
        request = {"n": n, "edges": edges}
        medians, costs = {}, {}
        for name, func in (("kruskal", A.kruskal), ("prim", A.prim)):
            _, result = timed(func, request)                 # warm-up, not recorded
            times = []
            for _ in range(RUNS):
                elapsed, result = timed(func, request)
                times.append(elapsed * 1000)
            medians[name] = (statistics.median(times), times)
            costs[name] = (result["cost"], result["components"])
        assert costs["kruskal"] == costs["prim"], "Kruskal and Prim disagree"
        rows.append((n, m, medians, costs["kruskal"]))

    lines = ["# Benchmark: Kruskal vs Prim", "",
             f"- Command: `python tests/benchmark.py` (seed `{SEED}`, graph for size n uses seed `{SEED} + n`)",
             f"- Inputs: random multigraphs (loops and parallel edges allowed), weights uniform in [-1e9, 1e9]",
             f"- Environment: Python {platform.python_version()}, {platform.system()} {platform.release()}, "
             f"CPU {cpu_name()}, {os.cpu_count()} logical CPUs",
             "- Timer: `time.perf_counter`; 1 warm-up call (not recorded) + 5 timed runs per method and size",
             "- Boundary: only the algorithm call on a prepared request dict; JSON parsing, generation and",
             "  output excluded; no compilation step in Python",
             "", "| n | m | Kruskal runs (ms) | Kruskal median (ms) | Prim runs (ms) | Prim median (ms) | Prim / Kruskal | MST cost | components |",
             "|---:|---:|---|---:|---|---:|---:|---:|---:|"]
    for n, m, med, (cost, comps) in rows:
        k, p = med["kruskal"], med["prim"]
        lines.append(f"| {n} | {m} | {', '.join(f'{t:.1f}' for t in k[1])} | {k[0]:.1f} | "
                     f"{', '.join(f'{t:.1f}' for t in p[1])} | {p[0]:.1f} | {p[0] / k[0]:.2f} | {cost} | {comps} |")
    text = "\n".join(lines) + "\n"
    with open(os.path.join(HERE, "benchmark_results.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
