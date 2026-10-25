"""Implement the six graph methods and your route helper. See the README at the repository root."""

import heapq


def dsu(request):
    n = request["n"]
    operations = request["operations"]

    components = n
    largest = 1 if n > 0 else 0
    result = []

    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]

        while parent[x] != root:
            parent[x], x = root, parent[x]

        return root

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return False

        if size[root_a] < size[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a
        size[root_a] += size[root_b]

        return True

    for a, b in operations:
        if union(a, b):
            components -= 1
            root = find(a)
            largest = max(largest, size[root])

        result.append([components, largest])

    return {"states": result}


def kruskal(request):
    """Separate Kruskal implementation; return cost, edge_ids, components."""
    n = request["n"]
    edges = request["edges"]

    components = n
    cost = 0
    edge_ids = []

    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]

        while parent[x] != root:
            parent[x], x = root, parent[x]

        return root

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return False

        if size[root_a] < size[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a
        size[root_a] += size[root_b]

        return True

    order = sorted(range(len(edges)), key=lambda i: edges[i][2])

    for i in order:
        u, v, w = edges[i]

        if union(u, v):
            components -= 1
            cost += w
            edge_ids.append(i)

    return {"cost": cost, "edge_ids": edge_ids, "components": components}


def prim(request):
    """Separate Prim implementation; restart for every unvisited component."""
    n = request["n"]
    edges = request["edges"]

    components = 0
    cost = 0
    edge_ids = []

    graph = [[] for _ in range(n)]
    visited = [False] * n

    for i, (u, v, w) in enumerate(edges):
        if u != v:
            graph[u].append((w, v, i))
            graph[v].append((w, u, i))

    for start in range(n):
        if visited[start]:
            continue

        components += 1
        visited[start] = True

        heap = list(graph[start])
        heapq.heapify(heap)

        while heap:
            w, v, i = heapq.heappop(heap)

            if visited[v]:
                continue

            visited[v] = True
            cost += w
            edge_ids.append(i)

            for item in graph[v]:
                if not visited[item[1]]:
                    heapq.heappush(heap, item)

    return {"cost": cost, "edge_ids": edge_ids, "components": components}


def scc(request):
    """Kosaraju with two DFS passes; return component and condensation."""
    n = request["n"]
    edges = request["edges"]

    graph = [[] for _ in range(n)]
    transpose = [[] for _ in range(n)]

    for u, v in edges:
        graph[u].append(v)
        transpose[v].append(u)

    visited = [False] * n
    next_index = [0] * n
    finish_order = []

    for start in range(n):
        if visited[start]:
            continue

        visited[start] = True
        stack = [start]

        while stack:
            u = stack[-1]

            if next_index[u] < len(graph[u]):
                v = graph[u][next_index[u]]
                next_index[u] += 1

                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
            else:
                finish_order.append(u)
                stack.pop()

    component = [-1] * n
    count = 0

    for start in reversed(finish_order):
        if component[start] != -1:
            continue

        component[start] = count
        stack = [start]

        while stack:
            u = stack.pop()

            for v in transpose[u]:
                if component[v] == -1:
                    component[v] = count
                    stack.append(v)

        count += 1

    pairs = set()

    for u, v in edges:
        if component[u] != component[v]:
            pairs.add((component[u], component[v]))

    condensation = [[a, b] for a, b in sorted(pairs)]

    return {"component": component, "condensation": condensation}


def topo(request):
    """Three-state DFS and reverse finish order; return acyclic and order."""
    n = request["n"]
    edges = request["edges"]

    graph = [[] for _ in range(n)]

    for u, v in edges:
        graph[u].append(v)

    order = topological_order(n, graph)

    if order is None:
        return {"acyclic": False, "order": []}

    return {"acyclic": True, "order": order}


def topological_order(n, graph):
    state = [0] * n
    next_index = [0] * n
    finish_order = []

    for start in range(n):
        if state[start] != 0:
            continue

        state[start] = 1
        stack = [start]

        while stack:
            u = stack[-1]

            if next_index[u] < len(graph[u]):
                v = graph[u][next_index[u]]
                next_index[u] += 1

                if state[v] == 1:
                    return None

                if state[v] == 0:
                    state[v] = 1
                    stack.append(v)
            else:
                state[u] = 2
                finish_order.append(u)
                stack.pop()

    finish_order.reverse()
    return finish_order


def dag(request):
    """Whole-graph cycle check and DAG relaxation; add your own route helper."""
    n = request["n"]
    source = request["source"]
    edges = request["edges"]

    graph = [[] for _ in range(n)]
    plain = [[] for _ in range(n)]

    for i, (u, v, w) in enumerate(edges):
        graph[u].append((v, w, i))
        plain[u].append(v)

    order = topological_order(n, plain)

    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}

    distance = [None] * n
    parent_edge = [-1] * n
    distance[source] = 0

    for u in order:
        if distance[u] is None:
            continue

        for v, w, i in graph[u]:
            new_distance = distance[u] + w

            if distance[v] is None or new_distance < distance[v]:
                distance[v] = new_distance
                parent_edge[v] = i

    return {"acyclic": True, "distance": distance, "parent_edge": parent_edge}


def route(edges, source, parent_edge, target):

    if target == source:
        return [source], []

    if parent_edge[target] == -1:
        return [], []

    vertices = [target]
    edge_ids = []
    current = target

    while current != source:
        edge_id = parent_edge[current]
        edge_ids.append(edge_id)
        current = edges[edge_id][0]
        vertices.append(current)

    vertices.reverse()
    edge_ids.reverse()

    return vertices, edge_ids