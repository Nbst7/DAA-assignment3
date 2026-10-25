# ANALYSIS: DAA Assignment 3, Graph Algorithms (Python)

Language: Python 3.12 (`submission.json` contains `{"language":"Python"}`). Code: `src/Python/algorithms.py`
(six methods plus `topological_order` and the route helper `route`). The entry point `src/Python/main.py`
is the supplied adapter and was not changed.

## Build, run and test commands

Python needs no compilation. Run all commands from the repository root.

| Purpose | Command |
|---|---|
| Launch check | `python tools/run.py --setup` |
| 36 public cases + state reset | `python tools/run.py --check` |
| Run the program on a JSON Lines file | `python tools/run.py --input tests/my_cases.jsonl` |
| All own tests (26 tests, about 8 s) | `python -m unittest discover -s tests -v` |
| Regenerate case inputs, actual outputs, `tests/CASES.md` | `python tests/write_cases.py` |
| Benchmark Kruskal vs Prim | `python tests/benchmark.py` |

## Common design decisions

**State reset.** No function uses module-level or global mutable state. Every call creates its own local lists
(`parent`, `size`, `graph`, `visited`, `distance`, ...), and `main.handle` only dispatches, so one request can never
see data from another. `tests/test_algorithms.py::RepeatedMixedRequests` sends the same mixed batch (including
`ping`) three times through one `main.py` process and checks that the three result blocks are identical, that
there is exactly one output line per request, and that a later DSU request is not affected by an earlier one.
`python tools/run.py --check` repeats the same idea with its own "two complete batches in one process" case.

**Deep DFS.** No algorithm is recursive. Every DFS (Kosaraju first pass, topological sort/cycle detection) keeps an
explicit stack of vertices plus a per-vertex pointer `next_index[u]` to the next neighbour to examine, so each
adjacency list is scanned once and the Python recursion limit is never touched. The second Kosaraju pass only needs
reachability, so it uses a plain stack. `find` in DSU is iterative (find root, then compress). Tests run chains of
100 000 vertices through every method (`DeepChains`).

**Numbers.** Python integers are unbounded, so sums up to 99 999 * 10^9 (about 10^14, far above 2^32) are exact.
`DeepChains` checks this for Kruskal, Prim and DAG distances. Unreachable DAG distance is `None` (JSON `null`).

## dsu

*Steps.* `parent[i] = i`, `size[i] = 1`. For each pair `[u, v]`, find both roots (path compression); if different,
attach the smaller tree below the larger (union by size), add sizes, decrement `components` and update `largest`
with the new root's size; append `[components, largest]` after every operation (also when nothing merged).

*Invariants.* Each root's `size` equals the number of vertices of its set; `components` equals the number of roots;
`largest` is the maximum set size seen so far, which is also the current maximum because sizes never shrink.

*Correctness.* Unions only merge two different sets, so the counter changes exactly when two different roots are
joined. Loops (`u == v`) and repeated pairs have equal roots and change nothing.

*Boundary cases.* `n = 0` gives `largest = 0` and no states unless operations exist (they cannot refer to vertices);
`n = 1`; loops; repeated unions; 250 000 operations on 100 000 vertices.

*Complexity.* Time O((n + q) alpha(n)) for q operations, memory O(n) plus the O(q) output.

## kruskal

*Steps.* Sort edge ids by weight (original positions are kept, so `edge_ids` are original IDs). Scan in
non-decreasing order; take edge `i` if its endpoints are in different DSU sets and merge them. `components = n - taken`.

*Invariants.* The chosen edges form a forest. After processing all edges of weight < x, the chosen forest has the
same connectivity as the graph restricted to those edges.

*Correctness.* Cycle/cut property: the lightest edge crossing a cut between two sets is in some minimum spanning
forest, and an edge whose endpoints are already connected is the heaviest edge on a cycle of the chosen edges plus
itself, so skipping it is safe. Negative weights need no special handling because only the order matters. A loop
always has equal roots, so it is never chosen, even when its weight is negative. Because every edge that
connects two sets is taken, the result spans each component, so it has `n - c` edges for `c` components (isolated
vertices count as components).

*Boundary cases.* `n = 0`, `n = 1` with only a loop, no edges, parallel edges, negative weights, ties (any optimal
forest is valid).

*Complexity.* Time O(m log m + m alpha(n)); memory O(n + m) (sorted id list, DSU arrays).

## prim

*Steps.* Build adjacency lists `(weight, neighbour, edge_id)` for both directions, skipping loops. For every
vertex `start` still unvisited, count a new component, mark it visited, push its edges into a min-heap and repeat:
pop the lightest edge; if its far end is already visited discard it (lazy deletion), otherwise visit it, add
the weight and edge id, and push its edges to unvisited neighbours.

*Invariants.* The visited vertices of the current component form a tree built from the chosen edges; the heap
contains every edge leaving this tree (plus stale entries to visited vertices).

*Correctness.* The popped valid edge is the lightest edge crossing the cut (tree, rest of component), so it is safe
by the cut property. Restarting from each unvisited vertex gives one tree per component, i.e. a minimum spanning
forest; an isolated vertex has an empty heap and is just counted.

*Boundary cases.* As Kruskal; additionally 690 components in the 100 000/250 000 random benchmark graph, which makes
the restart logic matter.

*Complexity.* Time O(n + m log m) = O(m log n) with a binary heap; memory O(n + m) (adjacency, heap up to 2m entries).

## scc (Kosaraju)

*Steps.* Build the graph and its transpose. Pass 1: iterative DFS over all vertices of the original graph, appending a
vertex to `finish_order` when all its neighbours are done. Pass 2: take vertices in reverse finish order; each still
unlabelled vertex starts a DFS on the transpose and labels everything it reaches with a new component number. Then
collect the set of pairs `(component[u], component[v])` for edges whose labels differ and output them sorted.

*Invariants.* Pass 1: a vertex is appended only after all vertices reachable from it were visited. Pass 2: when a DFS
starts, all components that can be reached from it in the original graph (i.e. which can reach it in the transpose)
are already labelled.

*Correctness.* The unlabelled vertex with the latest finish time lies in a source component of the remaining
condensation. In the transpose, edges of the condensation are reversed, so the DFS from it stays inside its own
component and labels exactly that component. Repeating this labels all components. The set of pairs contains each
cross-component pair once and never an internal pair.

*Boundary cases.* `n = 0`, loops (internal), duplicate edges (set removes duplicate pairs), isolated vertices
(singleton components), a 100 000-vertex chain (all singletons) and a closed ring (one component).

*Complexity.* Time O(n + m) for the two passes plus O(c log c) to sort c <= m distinct pairs; memory O(n + m).

## topo

*Steps.* Iterative DFS with colours white/gray/black. Entering a vertex colours it gray and pushes it; examining an edge
`u -> v`: gray `v` means a directed cycle (this includes a self loop), white `v` is entered, black `v` is ignored.
When all neighbours are done, colour the vertex black and append it to the finish list. The answer is the reversed
finish list, or `acyclic = false` with an empty order.

*Invariants.* Gray vertices are exactly the vertices on the current DFS stack and form a path; black vertices have all
their descendants finished.

*Correctness.* A directed cycle exists iff DFS meets an edge into a gray vertex (a back edge). If there is no back
edge, for every edge `u -> v` the vertex `v` finishes before `u`, so the reversed finish order puts `u` before `v`.
The loop starts DFS from every white vertex, so a cycle in any component, reachable or not, is found.

*Boundary cases.* `n = 0`, isolated vertices, self loops, parallel edges, a cycle in a different component, a
100 000-vertex chain, a closed 100 000-ring.

*Complexity.* Time O(n + m); memory O(n + m).

## dag

*Steps.* Run `topological_order` on the whole graph. If it finds a cycle, return `acyclic = false` and two empty
arrays. Otherwise set `distance[source] = 0`, `parent_edge = -1` everywhere and process vertices in topological order;
skip vertices with `distance = None` (unreachable); relax each outgoing edge `u -> v` when
`distance[u] + w < distance[v]` (or `distance[v]` is `None`) and store the original edge id in `parent_edge[v]`.

*Invariants.* When `u` is processed, all of its predecessors were processed, so `distance[u]` is final. For every
reached `v` other than the source, `parent_edge[v]` is an edge into `v` whose tail has `distance[tail] + w =
distance[v]`.

*Correctness.* In topological order each edge is relaxed after its tail has its final distance, so one pass gives
shortest paths even with negative weights (no cycles exist). Unreachable vertices are never relaxed from, so
negative edges among them cannot create a fake distance. The cycle check covers the whole graph, therefore a cycle that
the source cannot reach still gives `acyclic = false`, as required.

*Boundary cases.* `n = 1`; unreachable vertices (`null`, `-1`); negative edges outside the reachable part; ties and
parallel edges (strict `<` keeps the first found edge, any witness is valid); 64-bit sums on a 100 000 chain; cycle
unreachable from the source.

*Complexity.* Time O(n + m), memory O(n + m).

### Route helper

`route(edges, source, parent_edge, target)` returns `(vertices, edge_ids)`. It follows `parent_edge` from `target` back
to `source` using the original edge ids, then reverses the lists. Source gives `([source], [])`; an unreachable target
gives `([], [])` (my chosen convention). Time O(path length). Real calls (all in `tests/test_algorithms.py::RouteHelper`):

Graph `n=5`, `source=0`, `edges=[[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]` gives `distance=[0,3,-4,0,null]`,
`parent_edge=[-1,0,2,3,-1]`:

| Call | Result |
|---|---|
| `route(edges, 0, parent_edge, 3)` (reachable) | `([0, 1, 2, 3], [0, 2, 3])`, cost 3 - 7 + 4 = 0 = `distance[3]` |
| `route(edges, 0, parent_edge, 0)` (source) | `([0], [])` |
| `route(edges, 0, parent_edge, 4)` (unreachable) | `([], [])` |

Tied and parallel edges: `n=4`, `source=0`, `edges=[[0,1,2],[0,1,2],[0,2,4],[1,2,2],[2,3,1]]` gives
`distance=[0,2,4,5]`, `parent_edge=[-1,0,2,4]`. `route(edges, 0, parent_edge, 3)` returns `([0, 2, 3], [2, 4])`
with cost 4 + 1 = 5. Edges 0 and 1 are parallel and tie; the path 0->1->2 also costs 4 and ties with edge 2.
Strict `<` keeps the first one found, but `[0,1,2,3]` with edge ids `[0,3,4]` is an equally valid answer, and the
tests accept any witness whose edge ends and total cost match.

## Tests

Details and justification for every hand-made case are in `tests/CASES.md` (inputs, expected, actual), the commands
are in `tests/README.md`.

- **Hand cases** (`tests/my_cases.py`, 22 cases, MST ones run for both algorithms): empty graph, single vertex, loops,
  parallel edges, negative weights, isolates, duplicate SCC edges, self-loop and disconnected cycles for topo, DAG with
  unreachable vertices, ties and a cycle unreachable from the source.
- **Independent oracles** (`tests/oracles.py`, never imports `algorithms.py`): brute-force MST by subset enumeration,
  Floyd-Warshall and an iterative Tarjan for SCC, Kahn's algorithm for cycles/topological order, DP in Kahn order for DAG
  distances, naive relabelling and a no-union-by-size DSU. Validators check witnesses, so any valid optimal forest,
  SCC labelling, topological order or shortest-path witness passes.
- **Random cross-checks**: 200 to 300 random small graphs per task (fixed seed `20261025`).
- **Non-unique answers**: `test_alternative_valid_answers_are_accepted` (two optimal forests, three tied DAG witnesses,
  three topological orders, a relabelled SCC) and `test_invalid_witnesses_are_rejected` (cycle in the forest,
  non-optimal cost, duplicate/out-of-range ids, wrong parent edge, order violating an edge, merged or duplicated SCC
  output).
- **Deep chains and full limits**: chains of 100 000 vertices for all six methods; `n = 100 000`, `m = 250 000` random
  graphs (weights up to +-10^9) for DSU, Kruskal, Prim (equal cost and components), SCC (against Tarjan), topo (DAG and DAG
  plus one back edge) and DAG; a 100 000-vertex graph with a cycle unreachable from the source.
- **Repeated mixed requests**: the same 11-request batch three times in one process, plus random interleavings.
- **Sanity check of the tests themselves**: I temporarily broke the code in several ways (Kruskal accepting loops, Prim
  without restart, SCC with duplicate pairs, topo ignoring back edges to gray vertices, DAG never relaxing, DSU `largest`
  wrong) and every change made at least one test fail.

Result in the environment below: `python -m unittest discover -s tests -v` runs 26 tests and prints `OK` in about 8 s;
`python tools/run.py --check` passes all 36 public cases and the state-reset check.

## Benchmark: Kruskal vs Prim

Full output is in `tests/benchmark_results.md` (`python tests/benchmark.py`).

- **Inputs:** random multigraphs with loops and parallel edges, weights uniform in [-10^9, 10^9], seed `20261025`
  (the graph of size n uses `20261025 + n`). Sizes (n, m): (1 000, 5 000), (10 000, 50 000), (100 000, 250 000).
- **Environment:** Python 3.12.10, Windows 11, AMD64 CPU (Family 25 Model 68, AuthenticAMD), 16 logical CPUs.
- **Timer and protocol:** `time.perf_counter`; one untimed warm-up call per method and size, then 5 timed runs; the median
  is reported. Kruskal and Prim receive the same request dict and must return the same cost and component count (checked
  by an assertion).
- **Timing boundary:** only the call `algorithms.kruskal(request)` or `algorithms.prim(request)`; graph generation, JSON
  parsing and output are excluded. Python has no compilation step.

| n | m | Kruskal median (ms) | Prim median (ms) | Prim / Kruskal | components |
|---:|---:|---:|---:|---:|---:|
| 1 000 | 5 000 | 3.7 | 10.6 | 2.84 | 1 |
| 10 000 | 50 000 | 43.7 | 104.3 | 2.39 | 1 |
| 100 000 | 250 000 | 334.1 | 837.2 | 2.51 | 690 |

Individual runs: Kruskal 3.0 to 4.6 ms, 38.5 to 60.7 ms, 327.6 to 374.6 ms; Prim 8.7 to 11.6 ms, 96.9 to 127.5 ms,
819.5 to 903.2 ms.

*Observations.* Both methods are about O(m log m), and Kruskal was 2.4 to 2.8 times faster than Prim at all three
sizes; the ratio does not grow with size. A likely reason (not measured separately) is the constant factor in Python:
Kruskal does one C-level sort of integer ids plus cheap DSU operations, while Prim builds 2m adjacency tuples and does
many tuple-comparing heap pushes and pops. Both returned the same cost and component count on every graph (checked by an
assertion). *Limits of the measurement:* one personal computer with other programs running (the runs of Kruskal at
n = 10 000 vary from 38.5 to 60.7 ms, which is why medians are used), only sparse random graphs (m about 2.5 n), only
three sizes and five runs, so the numbers show an order of magnitude and should not be generalised to dense graphs or
other languages.

## Sources and AI assistance

Sources: course lectures on DSU, MST, DFS, Kosaraju and DAG shortest paths; the assignment specification and template
repository `RZhaniya/daa-assignment-3-graphs`; Python standard library documentation (`heapq`, `unittest`).

AI assistance: Claude (Anthropic) was used as a coding and writing assistant: it drafted the implementation in
`src/Python/algorithms.py` (based on my own DSU solution), the own tests and oracles in `tests/`, the benchmark script and
the first version of this document. I ran the commands, reviewed the results and I am responsible for the submitted
work and its explanations.
