#!/usr/bin/env python3
"""Week 5 · Task 3 — PageRank on a graph that will not fit as a matrix.

Textbook §5.2 (efficient PageRank), §5.2.1 - §5.2.3.

`DenseMatrix` is PageRank written the way the equations are written: build M,
multiply. It is correct, it is easy to read, and it stores n^2 numbers for a
graph with almost no edges.

The sparse implementation below keeps the supplied adjacency list and two
rank vectors instead of materialising the mostly-zero transition matrix.

    python3 bench.py
    python3 bench.py --yours
"""


class DenseMatrix:
    """PageRank as written in the equations. Stores n^2 floats."""

    def __init__(self, beta=0.85, tol=1e-10, max_iter=100):
        self.beta, self.tol, self.max_iter = beta, tol, max_iter

    def run(self, graph):
        nodes = list(graph)
        n = len(nodes)
        index = {v: i for i, v in enumerate(nodes)}

        # the full transition matrix, zeros and all
        M = [[0.0] * n for _ in range(n)]
        for v, outs in graph.items():
            if outs:
                share = 1.0 / len(outs)
                for w in outs:
                    M[index[w]][index[v]] = share
            else:
                for i in range(n):           # dead end: spread it everywhere
                    M[i][index[v]] = 1.0 / n

        r = [1.0 / n] * n
        for self.iterations in range(1, self.max_iter + 1):
            nr = [0.0] * n
            for i in range(n):
                row = M[i]
                s = 0.0
                for j in range(n):
                    if row[j]:
                        s += row[j] * r[j]
                nr[i] = self.beta * s + (1 - self.beta) / n
            delta = sum(abs(a - b) for a, b in zip(nr, r))
            r = nr
            if delta < self.tol:
                break
        return {v: r[index[v]] for v in nodes}

    def memory_floats(self):
        return getattr(self, "_n", 0) ** 2


class YourPageRank:
    """Sparse PageRank using the graph's adjacency-list representation.

    The implementation stores no n-by-n transition matrix. During iteration it
    keeps only the current and next rank vectors. The teleport contribution and
    the redistributed dead-end mass are each a single value shared by all
    nodes, so neither requires a dense matrix operation.
    """

    def __init__(self, beta=0.85, tol=1e-10, max_iter=100):
        if not 0.0 <= beta <= 1.0:
            raise ValueError("beta must be between 0 and 1")
        if tol < 0:
            raise ValueError("tol must be non-negative")
        if max_iter < 0:
            raise ValueError("max_iter must be non-negative")

        self.beta = beta
        self.tol = tol
        self.max_iter = max_iter
        self.iterations = 0
        self._memory_floats = 0

    def run(self, graph):
        nodes = list(graph)
        n = len(nodes)

        if n == 0:
            self.iterations = 0
            self._memory_floats = 0
            return {}

        index = {node: i for i, node in enumerate(nodes)}

        # Convert page names to integer positions once. These are adjacency
        # indices, not floating-point matrix entries.
        outgoing = [
            tuple(index[target] for target in graph[node])
            for node in nodes
        ]

        ranks = [1.0 / n] * n
        self._memory_floats = n
        self.iterations = 0

        teleport = (1.0 - self.beta) / n

        for step in range(1, self.max_iter + 1):
            # Dead ends behave as if they link uniformly to every page. Their
            # total contribution is one shared scalar, not n separate columns.
            dangling_rank = sum(
                ranks[i]
                for i, targets in enumerate(outgoing)
                if not targets
            )

            common = teleport + self.beta * dangling_rank / n
            new_ranks = [common] * n

            # At this point the largest floating-point state is the two rank
            # vectors plus a few shared scalar values.
            self._memory_floats = max(
                self._memory_floats,
                2 * n + 6
            )

            # Push rank along only the edges that actually exist: O(n + m)
            # work per iteration instead of scanning n^2 matrix positions.
            for source, targets in enumerate(outgoing):
                if not targets:
                    continue

                share = self.beta * ranks[source] / len(targets)
                for target in targets:
                    new_ranks[target] += share

            delta = sum(
                abs(new_ranks[i] - ranks[i])
                for i in range(n)
            )

            ranks = new_ranks
            self.iterations = step

            if delta < self.tol:
                break

        return {
            node: ranks[i]
            for i, node in enumerate(nodes)
        }

    def memory_floats(self):
        """Largest number of floating-point values held during iteration."""
        return self._memory_floats
