"""Independent oracles and answer validators for the own tests (do not import algorithms.py)."""

import itertools


def int64(x):
    return type(x) is int and -(1 << 63) <= x < (1 << 63)


# ------------------------------------------------------------------ helpers

def undirected_components(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = find(e[0]), find(e[1])
        if a != b:
            parent[a] = b
    return len({find(i) for i in range(n)}), find


def same_partition(a, b):
    if len(a) != len(b):
        return False
    fwd, rev = {}, {}
    for x, y in zip(a, b):
        if fwd.setdefault(x, y) != y or rev.setdefault(y, x) != x:
            return False
    return True


def kahn(n, edges):
    """Kahn's algorithm: topological order or None if the graph has a directed cycle."""
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for e in edges:
        adj[e[0]].append(e[1])
        indeg[e[1]] += 1
    queue = [v for v in range(n) if indeg[v] == 0]
    order = []
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return order if len(order) == n else None


# ------------------------------------------------------------------ DSU

def dsu_oracle(n, operations):
    """Unconditional linking with path halving (no union by size) plus explicit sizes."""
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    comps, largest, states = n, (1 if n else 0), []
    for u, v in operations:
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b
            size[b] += size[a]
            comps -= 1
            largest = max(largest, size[b])
        states.append([comps, largest])
    return states


def dsu_naive(n, operations):
    label = list(range(n))
    comps, states = n, []
    for u, v in operations:
        a, b = label[u], label[v]
        if a != b:
            label = [a if x == b else x for x in label]
            comps -= 1
        counts = {}
        for x in label:
            counts[x] = counts.get(x, 0) + 1
        states.append([comps, max(counts.values()) if counts else 0])
    return states


# ------------------------------------------------------------------ MST

def brute_mst(n, edges):
    comps, _ = undirected_components(n, edges)
    need = n - comps
    best = None
    for subset in itertools.combinations(range(len(edges)), need):
        c, _ = undirected_components(n, [edges[i] for i in subset])
        if c == comps:
            cost = sum(edges[i][2] for i in subset)
            if best is None or cost < best:
                best = cost
    return best, comps


def valid_forest(n, edges, ans, cost, comps):
    """The answer must be a spanning forest with the given optimal cost."""
    try:
        if not (int64(ans["cost"]) and int64(ans["components"])):
            return False
        ids = ans["edge_ids"]
        if ans["cost"] != cost or ans["components"] != comps:
            return False
        if not all(type(i) is int and 0 <= i < len(edges) for i in ids):
            return False
        if len(set(ids)) != len(ids) or len(ids) != n - comps:
            return False
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        total = 0
        for i in ids:
            u, v, w = edges[i]
            a, b = find(u), find(v)
            if a == b:
                return False          # cycle (or loop) inside the forest
            parent[a] = b
            total += w
        if total != cost:
            return False
        return all(find(u) == find(v) for u, v, _ in edges)   # spans every component
    except (KeyError, TypeError, IndexError):
        return False


# ------------------------------------------------------------------ SCC

def floyd_labels(n, edges):
    reach = [[i == j for j in range(n)] for i in range(n)]
    for u, v in edges:
        reach[u][v] = True
    for k in range(n):
        for i in range(n):
            if reach[i][k]:
                for j in range(n):
                    if reach[k][j]:
                        reach[i][j] = True
    labels = [-1] * n
    c = 0
    for i in range(n):
        if labels[i] == -1:
            for j in range(n):
                if reach[i][j] and reach[j][i]:
                    labels[j] = c
            c += 1
    return labels


def tarjan_labels(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    index = [-1] * n
    low = [0] * n
    on = [False] * n
    ptr = [0] * n
    labels = [-1] * n
    st = []
    counter = comp = 0
    for s in range(n):
        if index[s] != -1:
            continue
        index[s] = low[s] = counter
        counter += 1
        st.append(s)
        on[s] = True
        work = [s]
        while work:
            u = work[-1]
            if ptr[u] < len(adj[u]):
                v = adj[u][ptr[u]]
                ptr[u] += 1
                if index[v] == -1:
                    index[v] = low[v] = counter
                    counter += 1
                    st.append(v)
                    on[v] = True
                    work.append(v)
                elif on[v]:
                    low[u] = min(low[u], index[v])
            else:
                work.pop()
                if work:
                    low[work[-1]] = min(low[work[-1]], low[u])
                if low[u] == index[u]:
                    while True:
                        w = st.pop()
                        on[w] = False
                        labels[w] = comp
                        if w == u:
                            break
                    comp += 1
    return labels


def valid_scc(n, edges, ans, reference_labels):
    try:
        labels = ans["component"]
        if len(labels) != n or not all(type(x) is int and x >= 0 for x in labels):
            return False
        if not same_partition(labels, reference_labels):
            return False
        pairs = [tuple(p) for p in ans["condensation"]]
        if len(set(pairs)) != len(pairs):
            return False                       # duplicate cross pair
        expected = {(labels[u], labels[v]) for u, v in edges if labels[u] != labels[v]}
        return set(pairs) == expected          # no internal pairs, none missing
    except (KeyError, TypeError, IndexError):
        return False


# ------------------------------------------------------------------ topo

def valid_topo(n, edges, ans):
    try:
        order = kahn(n, edges)
        if order is None:
            return ans["acyclic"] is False and ans["order"] == []
        if ans["acyclic"] is not True:
            return False
        got = ans["order"]
        if sorted(got) != list(range(n)):
            return False
        pos = {v: i for i, v in enumerate(got)}
        return all(pos[u] < pos[v] for u, v in edges)
    except (KeyError, TypeError):
        return False


# ------------------------------------------------------------------ DAG

def dag_oracle_distance(n, source, edges):
    """Distances via DP in Kahn order; None if the whole graph has a directed cycle."""
    order = kahn(n, [(e[0], e[1]) for e in edges])
    if order is None:
        return None
    out = [[] for _ in range(n)]
    for u, v, w in edges:
        out[u].append((v, w))
    dist = [None] * n
    dist[source] = 0
    for u in order:
        if dist[u] is None:
            continue
        for v, w in out[u]:
            if dist[v] is None or dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist


def valid_dag(n, source, edges, ans):
    try:
        dist = dag_oracle_distance(n, source, edges)
        if dist is None:
            return ans["acyclic"] is False and ans["distance"] == [] and ans["parent_edge"] == []
        if ans["acyclic"] is not True or ans["distance"] != dist:
            return False
        pe = ans["parent_edge"]
        if len(pe) != n:
            return False
        for v in range(n):
            if v == source or dist[v] is None:
                if pe[v] != -1:
                    return False
                continue
            e = pe[v]
            if type(e) is not int or not 0 <= e < len(edges):
                return False
            u, head, w = edges[e]
            if head != v or dist[u] is None or dist[u] + w != dist[v]:
                return False
        return True
    except (KeyError, TypeError, IndexError):
        return False
