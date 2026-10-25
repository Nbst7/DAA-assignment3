"""Own tests for DAA Assignment 3 (Python).

Run from the repository root:
    python -m unittest discover -s tests -v
"""

import json
import os
import random
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import algorithms as A          # noqa: E402
import main as M                # noqa: E402
import oracles as O             # noqa: E402
from my_cases import HAND_CASES  # noqa: E402

SEED = 20261025
BIG_N = 100000
BIG_M = 250000
W = 10 ** 9


def run(request):
    return M.handle(request)


def check(request, ans, expected=None):
    """Validate any answer by contract; compare unique fields with `expected` if given."""
    task = request["task"]
    n = request.get("n")
    if task == "dsu":
        ok = ans["states"] == O.dsu_oracle(n, request["operations"])
    elif task in ("kruskal", "prim"):
        if len(request["edges"]) <= 12:
            cost, comps = O.brute_mst(n, request["edges"])
        else:
            cost, comps = ans["cost"], O.undirected_components(n, request["edges"])[0]
        ok = O.valid_forest(n, request["edges"], ans, cost, comps)
    elif task == "scc":
        ref = O.floyd_labels(n, request["edges"]) if n <= 60 else O.tarjan_labels(n, request["edges"])
        ok = O.valid_scc(n, request["edges"], ans, ref)
    elif task == "topo":
        ok = O.valid_topo(n, request["edges"], ans)
    else:
        ok = O.valid_dag(n, request["source"], request["edges"], ans)
    if not ok:
        return False
    for key, value in (expected or {}).items():
        if key == "component":
            if not O.same_partition(ans[key], value):
                return False
        elif key == "condensation":
            continue                      # labels differ; valid_scc already checked the pairs
        elif key == "order":
            continue
        elif ans[key] != value:
            return False
    return True


def tasks_for(request):
    return ["kruskal", "prim"] if request["task"] == "kruskal" else [request["task"]]


# ====================================================================== hand cases

class HandCases(unittest.TestCase):
    def test_each_case(self):
        for case in HAND_CASES:
            request = case["request"]
            for task in tasks_for(request):
                req = dict(request, task=task)
                with self.subTest(case["name"], task=task):
                    self.assertTrue(check(req, run(req), case["expected"]), case["why"])

    def test_alternative_valid_answers_are_accepted(self):
        edges = [[0, 1, -5], [0, 1, 2], [1, 2, -1], [0, 2, -1]]
        for ids in ([0, 2], [0, 3]):                       # two different optimal forests
            ans = {"cost": -6, "edge_ids": ids, "components": 1}
            self.assertTrue(O.valid_forest(3, edges, ans, -6, 1))
        dag_edges = [[0, 1, 2], [0, 1, 2], [0, 2, 4], [1, 2, 2], [2, 3, 1]]
        for pe in ([-1, 0, 2, 4], [-1, 1, 3, 4], [-1, 0, 3, 4]):   # tied witnesses
            ans = {"acyclic": True, "distance": [0, 2, 4, 5], "parent_edge": pe}
            self.assertTrue(O.valid_dag(4, 0, dag_edges, ans))
        for order in ([0, 1, 2, 3], [3, 0, 1, 2], [0, 3, 1, 2]):
            ans = {"acyclic": True, "order": order}
            self.assertTrue(O.valid_topo(4, [[0, 1], [0, 1], [1, 2]], ans))
        ans = {"component": [7, 7, 3, 3, 9], "condensation": [[7, 3]]}   # relabelled SCC
        edges = [[0, 1], [1, 0], [1, 2], [2, 3], [3, 2], [0, 1], [4, 4]]
        self.assertTrue(O.valid_scc(5, edges, ans, [0, 0, 1, 1, 2]))

    def test_invalid_witnesses_are_rejected(self):
        edges = [[0, 1, -5], [0, 1, 2], [1, 2, -1], [0, 2, -1]]
        bad_forests = [
            {"cost": -6, "edge_ids": [0, 1], "components": 1},       # two parallel edges: cycle
            {"cost": -4, "edge_ids": [1, 2], "components": 1},       # not optimal
            {"cost": -6, "edge_ids": [0, 0], "components": 1},       # duplicate id
            {"cost": -6, "edge_ids": [0, 9], "components": 1},       # id out of range
            {"cost": -6, "edge_ids": [0], "components": 1},          # does not span
        ]
        for ans in bad_forests:
            self.assertFalse(O.valid_forest(3, edges, ans, -6, 1), ans)
        dag_edges = [[0, 1, 2], [0, 1, 2], [0, 2, 4], [1, 2, 2], [2, 3, 1]]
        bad_pe = [[-1, 0, 2, 3], [-1, 0, 2, 1], [0, 0, 2, 4], [-1, 0, 4, 4], [-1, 9, 2, 4]]
        for pe in bad_pe:   # wrong head, wrong source parent, wrong tail/cost, out of range
            ans = {"acyclic": True, "distance": [0, 2, 4, 5], "parent_edge": pe}
            self.assertFalse(O.valid_dag(4, 0, dag_edges, ans), pe)
        self.assertFalse(O.valid_topo(3, [[0, 1], [1, 2]], {"acyclic": True, "order": [1, 0, 2]}))
        self.assertFalse(O.valid_topo(3, [[0, 1], [1, 0]], {"acyclic": True, "order": [0, 1, 2]}))
        self.assertFalse(O.valid_scc(3, [[0, 1], [1, 0]], {"component": [0, 1, 1], "condensation": []},
                                     [0, 0, 1]))                                  # merged wrongly
        self.assertFalse(O.valid_scc(3, [[0, 1], [1, 2]],
                                     {"component": [0, 1, 2], "condensation": [[0, 1], [0, 1], [1, 2]]},
                                     [0, 1, 2]))                                  # duplicate pair
        self.assertFalse(O.valid_scc(3, [[0, 1], [1, 2]],
                                     {"component": [0, 1, 2], "condensation": [[0, 1]]},
                                     [0, 1, 2]))                                  # missing pair


# ====================================================================== random vs oracles

class RandomSmall(unittest.TestCase):
    def test_dsu(self):
        rng = random.Random(SEED)
        for _ in range(200):
            n = rng.randint(0, 12)
            ops = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randint(0, 15))] if n else []
            ans = run({"task": "dsu", "n": n, "operations": ops})
            self.assertEqual(ans["states"], O.dsu_naive(n, ops))
            self.assertEqual(ans["states"], O.dsu_oracle(n, ops))

    def test_mst(self):
        rng = random.Random(SEED + 1)
        for _ in range(300):
            n = rng.randint(0, 7)
            m = rng.randint(0, 9) if n else 0
            edges = [[rng.randrange(n), rng.randrange(n), rng.randint(-6, 6)] for _ in range(m)]
            for task in ("kruskal", "prim"):
                req = {"task": task, "n": n, "edges": edges}
                self.assertTrue(check(req, run(req)), (task, n, edges))

    def test_scc_and_oracle_agreement(self):
        rng = random.Random(SEED + 2)
        for _ in range(300):
            n = rng.randint(0, 9)
            m = rng.randint(0, 16) if n else 0
            edges = [[rng.randrange(n), rng.randrange(n)] for _ in range(m)]
            self.assertTrue(O.same_partition(O.floyd_labels(n, edges), O.tarjan_labels(n, edges)))
            req = {"task": "scc", "n": n, "edges": edges}
            self.assertTrue(check(req, run(req)), (n, edges))

    def test_topo(self):
        rng = random.Random(SEED + 3)
        for _ in range(300):
            n = rng.randint(0, 9)
            m = rng.randint(0, 14) if n else 0
            edges = [[rng.randrange(n), rng.randrange(n)] for _ in range(m)]
            if rng.random() < 0.5:   # bias towards DAGs
                edges = [[min(u, v), max(u, v)] for u, v in edges if u != v]
            req = {"task": "topo", "n": n, "edges": edges}
            self.assertTrue(check(req, run(req)), (n, edges))

    def test_dag(self):
        rng = random.Random(SEED + 4)
        for _ in range(300):
            n = rng.randint(1, 9)
            m = rng.randint(0, 16)
            edges = [[rng.randrange(n), rng.randrange(n), rng.randint(-9, 9)] for _ in range(m)]
            if rng.random() < 0.7:
                edges = [[min(u, v), max(u, v), w] for u, v, w in edges if u != v]
            req = {"task": "dag", "n": n, "source": rng.randrange(n), "edges": edges}
            self.assertTrue(check(req, run(req)), (n, req["source"], edges))


# ====================================================================== route helper

class RouteHelper(unittest.TestCase):
    def setUp(self):
        self.edges = [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]
        self.ans = run({"task": "dag", "n": 5, "source": 0, "edges": self.edges})

    def test_reachable_target(self):
        vertices, edge_ids = A.route(self.edges, 0, self.ans["parent_edge"], 3)
        self.assertEqual((vertices, edge_ids), ([0, 1, 2, 3], [0, 2, 3]))
        self.assertEqual(sum(self.edges[e][2] for e in edge_ids), self.ans["distance"][3])

    def test_source(self):
        self.assertEqual(A.route(self.edges, 0, self.ans["parent_edge"], 0), ([0], []))

    def test_unreachable_target(self):
        self.assertEqual(A.route(self.edges, 0, self.ans["parent_edge"], 4), ([], []))

    def test_tied_and_parallel_edges(self):
        edges = [[0, 1, 2], [0, 1, 2], [0, 2, 4], [1, 2, 2], [2, 3, 1]]
        ans = run({"task": "dag", "n": 4, "source": 0, "edges": edges})
        vertices, edge_ids = A.route(edges, 0, ans["parent_edge"], 3)
        self.assertEqual(vertices[0], 0)
        self.assertEqual(vertices[-1], 3)
        self.assertEqual(sum(edges[e][2] for e in edge_ids), 5)
        for e, (a, b) in zip(edge_ids, zip(vertices, vertices[1:])):
            self.assertEqual((edges[e][0], edges[e][1]), (a, b))
        self.assertEqual(len(set(edge_ids)), len(edge_ids))


# ====================================================================== deep chains

class DeepChains(unittest.TestCase):
    N = BIG_N

    def chain(self, weight=None):
        if weight is None:
            return [[i, i + 1] for i in range(self.N - 1)]
        return [[i, i + 1, weight] for i in range(self.N - 1)]

    def test_dsu_chain(self):
        ops = [[i, i + 1] for i in range(self.N - 1)]
        states = run({"task": "dsu", "n": self.N, "operations": ops})["states"]
        self.assertEqual(states[-1], [1, self.N])
        self.assertEqual(states[0], [self.N - 1, 2])

    def test_mst_chain_64_bit_cost(self):
        edges = self.chain(W)
        for task in ("kruskal", "prim"):
            ans = run({"task": task, "n": self.N, "edges": edges})
            self.assertEqual(ans["cost"], (self.N - 1) * W)
            self.assertEqual(ans["components"], 1)
            self.assertEqual(len(ans["edge_ids"]), self.N - 1)

    def test_scc_chain_and_closed_ring(self):
        ans = run({"task": "scc", "n": self.N, "edges": self.chain()})
        self.assertEqual(len(set(ans["component"])), self.N)
        self.assertEqual(len(ans["condensation"]), self.N - 1)
        ring = self.chain() + [[self.N - 1, 0]]
        ans = run({"task": "scc", "n": self.N, "edges": ring})
        self.assertEqual(len(set(ans["component"])), 1)
        self.assertEqual(ans["condensation"], [])

    def test_topo_chain_and_ring(self):
        ans = run({"task": "topo", "n": self.N, "edges": self.chain()})
        self.assertTrue(ans["acyclic"])
        self.assertEqual(ans["order"], list(range(self.N)))
        ring = self.chain() + [[self.N - 1, 0]]
        self.assertEqual(run({"task": "topo", "n": self.N, "edges": ring}),
                         {"acyclic": False, "order": []})

    def test_dag_chain_64_bit_distance(self):
        edges = self.chain(W)
        ans = run({"task": "dag", "n": self.N, "source": 0, "edges": edges})
        self.assertEqual(ans["distance"][-1], (self.N - 1) * W)
        self.assertEqual(ans["parent_edge"][-1], self.N - 2)
        vertices, edge_ids = A.route(edges, 0, ans["parent_edge"], self.N - 1)
        self.assertEqual(vertices, list(range(self.N)))
        self.assertEqual(len(edge_ids), self.N - 1)

    def test_dag_reversed_chain_from_the_end(self):
        edges = [[i + 1, i, -W] for i in range(self.N - 1)]       # n-1 -> n-2 -> ... -> 0
        ans = run({"task": "dag", "n": self.N, "source": self.N - 1, "edges": edges})
        self.assertEqual(ans["distance"][0], -(self.N - 1) * W)


# ====================================================================== full limits

def random_edges(rng, n, m, weighted=True):
    if weighted:
        return [[rng.randrange(n), rng.randrange(n), rng.randint(-W, W)] for _ in range(m)]
    return [[rng.randrange(n), rng.randrange(n)] for _ in range(m)]


class FullLimits(unittest.TestCase):
    def test_dsu_max(self):
        rng = random.Random(SEED + 10)
        ops = [[rng.randrange(BIG_N), rng.randrange(BIG_N)] for _ in range(BIG_M)]
        ans = run({"task": "dsu", "n": BIG_N, "operations": ops})
        self.assertEqual(ans["states"], O.dsu_oracle(BIG_N, ops))

    def test_kruskal_and_prim_max(self):
        rng = random.Random(SEED + 11)
        edges = random_edges(rng, BIG_N, BIG_M)
        results = {}
        for task in ("kruskal", "prim"):
            req = {"task": task, "n": BIG_N, "edges": edges}
            results[task] = run(req)
        self.assertEqual(results["kruskal"]["cost"], results["prim"]["cost"])
        self.assertEqual(results["kruskal"]["components"], results["prim"]["components"])
        comps = O.undirected_components(BIG_N, edges)[0]
        for task, ans in results.items():
            self.assertTrue(O.valid_forest(BIG_N, edges, ans, results["kruskal"]["cost"], comps), task)

    def test_scc_max(self):
        rng = random.Random(SEED + 12)
        edges = random_edges(rng, BIG_N, BIG_M, weighted=False)
        req = {"task": "scc", "n": BIG_N, "edges": edges}
        self.assertTrue(O.valid_scc(BIG_N, edges, run(req), O.tarjan_labels(BIG_N, edges)))

    def random_dag_edges(self, rng, weighted):
        perm = list(range(BIG_N))
        rng.shuffle(perm)
        edges = []
        while len(edges) < BIG_M:
            a, b = rng.randrange(BIG_N), rng.randrange(BIG_N)
            if a == b:
                continue
            u, v = perm[min(a, b)], perm[max(a, b)]
            edges.append([u, v, rng.randint(-W, W)] if weighted else [u, v])
        return edges

    def test_topo_max_dag_and_with_cycle(self):
        rng = random.Random(SEED + 13)
        edges = self.random_dag_edges(rng, weighted=False)
        self.assertTrue(O.valid_topo(BIG_N, edges, run({"task": "topo", "n": BIG_N, "edges": edges})))
        edges.append([edges[0][1], edges[0][0]])               # reverse of a DAG edge closes a cycle
        self.assertEqual(run({"task": "topo", "n": BIG_N, "edges": edges}), {"acyclic": False, "order": []})

    def test_dag_max(self):
        rng = random.Random(SEED + 14)
        edges = self.random_dag_edges(rng, weighted=True)
        req = {"task": "dag", "n": BIG_N, "source": edges[0][0], "edges": edges}
        self.assertTrue(O.valid_dag(BIG_N, req["source"], edges, run(req)))

    def test_dag_cycle_unreachable_from_source_at_scale(self):
        n = BIG_N
        edges = [[i, i + 1, 1] for i in range(n // 2 - 1)]                 # reachable chain from 0
        ring = list(range(n // 2, n))
        edges += [[ring[i], ring[(i + 1) % len(ring)], 1] for i in range(len(ring))]   # separate cycle
        ans = run({"task": "dag", "n": n, "source": 0, "edges": edges})
        self.assertEqual(ans, {"acyclic": False, "distance": [], "parent_edge": []})


# ====================================================================== state reset / transport

class RepeatedMixedRequests(unittest.TestCase):
    def batch(self):
        return [
            {"task": "ping"},
            {"task": "dsu", "n": 4, "operations": [[0, 1], [1, 2], [0, 2], [3, 3]]},
            {"task": "kruskal", "n": 4, "edges": [[0, 1, 4], [1, 2, 2], [0, 2, 3]]},
            {"task": "prim", "n": 4, "edges": [[0, 1, 4], [1, 2, 2], [0, 2, 3]]},
            {"task": "scc", "n": 5, "edges": [[0, 1], [1, 0], [1, 2], [2, 3], [3, 2], [4, 4]]},
            {"task": "topo", "n": 3, "edges": [[0, 1], [1, 2]]},
            {"task": "topo", "n": 3, "edges": [[0, 1], [1, 0]]},
            {"task": "dag", "n": 5, "source": 0, "edges": [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]},
            {"task": "dag", "n": 2, "source": 1, "edges": [[0, 1, 5]]},
            {"task": "dsu", "n": 2, "operations": [[0, 1]]},
            {"task": "ping"},
        ]

    def test_two_batches_in_one_process_are_identical(self):
        requests = self.batch() * 3
        data = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in requests)
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "src", "Python", "main.py")],
                              input=data, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = proc.stdout.splitlines()
        self.assertEqual(len(lines), len(requests))          # exactly one line per request
        results = [json.loads(line) for line in lines]
        size = len(self.batch())
        self.assertEqual(results[:size], results[size:2 * size])
        self.assertEqual(results[:size], results[2 * size:])
        self.assertEqual(results[0], {"status": "ready"})
        self.assertEqual(results[1]["states"], [[3, 2], [2, 3], [2, 3], [2, 3]])
        self.assertEqual(results[9]["states"], [[1, 2]])      # no leftover DSU state from request 1

    def test_interleaved_order_does_not_matter(self):
        rng = random.Random(SEED + 20)
        requests = self.batch()
        expected = [run(r) for r in requests]
        for _ in range(20):
            idx = [rng.randrange(len(requests)) for _ in range(12)]
            for i in idx:
                self.assertEqual(run(requests[i]), expected[i])


if __name__ == "__main__":
    unittest.main(verbosity=2)
