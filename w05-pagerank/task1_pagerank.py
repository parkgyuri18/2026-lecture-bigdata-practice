#!/usr/bin/env python3
"""Week 5 · Task 1 — PageRank, and the two ways it breaks.

Textbook §5.1 (PageRank), §5.1.3 (dead ends), §5.1.4 (spider traps).

PageRank is a random surfer following links forever, and the rank of a page is
how often the surfer is there. As one line of linear algebra it is
`r = M r`, and as written it does not work on the actual web.

Two structures break it, and the fix for both is the same one line. Build the
broken version first so you can see each failure, then fix it.

    python3 task1_pagerank.py --verify
"""
import argparse

# A: -> B, C      B: -> C      C: -> A
SIMPLE = {"A": ["B", "C"], "B": ["C"], "C": ["A"]}

# C has no out-links at all. Rank leaks out of the graph and everything -> 0.
DEAD_END = {"A": ["B", "C"], "B": ["C"], "C": []}

# C and D only point at each other. They absorb everything.
SPIDER_TRAP = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["C"]}


def pagerank(graph, beta=0.85, iterations=100, tol=1e-10):
    """Rank every node. Return {node: rank}, summing to 1.

    `beta` is the probability the surfer follows a link. With probability
    1 - beta they teleport to a node chosen uniformly.

    Dead-end rank is redistributed uniformly to every node. This is equivalent
    to treating a dead end as if it linked to every page. Teleportation prevents
    a spider trap from permanently absorbing all rank.

    Stop early when the L1 change is smaller than `tol`, and expose the number
    of iterations actually used through `pagerank.iterations`.
    """
    nodes = list(graph)
    n = len(nodes)

    if n == 0:
        pagerank.iterations = 0
        return {}

    if not 0.0 <= beta <= 1.0:
        raise ValueError("beta must be between 0 and 1")
    if iterations < 0:
        raise ValueError("iterations must be non-negative")
    if tol < 0:
        raise ValueError("tol must be non-negative")

    ranks = {node: 1.0 / n for node in nodes}
    pagerank.iterations = 0

    for step in range(1, iterations + 1):
        # Every node receives the same teleport contribution.
        base = (1.0 - beta) / n

        # A dead end has nowhere to send its rank. Treat it as linking to every
        # node so that its rank is conserved rather than leaking away.
        dangling_rank = sum(
            ranks[node]
            for node in nodes
            if not graph[node]
        )
        dangling_share = beta * dangling_rank / n

        new_ranks = {
            node: base + dangling_share
            for node in nodes
        }

        # Push each source page's rank only along its actual outgoing links.
        for source in nodes:
            outgoing = graph[source]
            if not outgoing:
                continue

            share = beta * ranks[source] / len(outgoing)
            for target in outgoing:
                new_ranks[target] += share

        change = sum(
            abs(new_ranks[node] - ranks[node])
            for node in nodes
        )

        ranks = new_ranks
        pagerank.iterations = step

        if change < tol:
            break

    return ranks


def pagerank_no_teleport(graph, iterations=100):
    """The deliberately broken PageRank version.

    It uses beta = 1, provides no teleportation, and drops rank that reaches a
    dead end. Consequently a dead end drains rank out of the graph and a spider
    trap can eventually absorb almost all remaining rank.
    """
    nodes = list(graph)
    n = len(nodes)

    if n == 0:
        return {}
    if iterations < 0:
        raise ValueError("iterations must be non-negative")

    ranks = {node: 1.0 / n for node in nodes}

    for _ in range(iterations):
        new_ranks = {node: 0.0 for node in nodes}

        for source in nodes:
            outgoing = graph[source]

            # Deliberately do nothing for a dead end: its rank disappears.
            if not outgoing:
                continue

            share = ranks[source] / len(outgoing)
            for target in outgoing:
                new_ranks[target] += share

        ranks = new_ranks

    return ranks


# ------------------------------------------------------------------- harness
def verify():
    fails = 0

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<48} {detail}")
        fails += not ok

    try:
        r = pagerank(SIMPLE)
    except NotImplementedError:
        print("  pagerank is still a stub"); return 1

    check("ranks sum to 1", abs(sum(r.values()) - 1) < 1e-6, f"{sum(r.values()):.6f}")
    check("every node ranked", set(r) == set(SIMPLE), sorted(r))
    # C is pointed at by both A and B, so it has to come first.
    check("C outranks A and B", r["C"] > r["A"] and r["C"] > r["B"],
          {k: round(v, 4) for k, v in sorted(r.items())})

    try:
        broken = pagerank_no_teleport(DEAD_END)
    except NotImplementedError:
        print("  pagerank_no_teleport is still a stub"); return 1
    check("without the fix, a dead end drains the graph",
          sum(broken.values()) < 0.5, f"total rank {sum(broken.values()):.4f}")

    fixed = pagerank(DEAD_END)
    check("with the fix, rank is conserved",
          abs(sum(fixed.values()) - 1) < 1e-6, f"{sum(fixed.values()):.6f}")

    trapped = pagerank_no_teleport(SPIDER_TRAP)
    check("without the fix, a spider trap takes everything",
          trapped["C"] + trapped["D"] > 0.95,
          f"C+D = {trapped['C'] + trapped['D']:.4f}")

    untrapped = pagerank(SPIDER_TRAP)
    check("with the fix, A and B keep some rank",
          untrapped["A"] > 0.01 and untrapped["B"] > 0.01,
          {k: round(v, 4) for k, v in sorted(untrapped.items())})

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
