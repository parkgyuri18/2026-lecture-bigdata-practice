# Task 2 · PageRank Convergence

## Test environment

- **Operating system:** Windows 11
- **CPU:** 12th Gen Intel(R) Core(TM) i5-1240P (`Intel64 Family 6 Model 154 Stepping 3`)
- **RAM:** 15.6 GB
- **Python:** 3.14.7
- **Programs open during measurement:** Visual Studio Code, KakaoTalk, File Explorer, Chrome, and ChatGPT

## A2–A3 · Iterations as beta changes

The following measurements used 1,200 nodes and an L1 convergence tolerance of `1e-10`.

| Beta | Iterations | Time (s) | First three pages |
|---:|---:|---:|---|
| 0.50 | 14 | 0.0164 | p00009, p00001, p00006 |
| 0.70 | 17 | 0.0170 | p00009, p00001, p00006 |
| 0.85 | 20 | 0.0222 | p00009, p00001, p00006 |
| 0.95 | 23 | 0.0258 | p00009, p00001, p00006 |
| 0.99 | 24 | 0.0271 | p00009, p00001, p00006 |

The iteration count increased from 14 to 24 as beta approached 1. A larger beta means that the random surfer follows links more often and teleports less often, so the teleportation-induced mixing is weaker and rank differences decay more slowly. The curve increased steadily, although the increase from beta 0.95 to 0.99 was only one additional iteration on this graph.

## A4 · Graph size, iteration count, and wall time

Before running the experiment, I expected graph size to increase wall time substantially because each iteration must scan more nodes and edges, while the number of iterations would remain similar if the larger generated graph had similar convergence properties. The results supported that prediction.

| Beta | Nodes | Tolerance | Iterations | Time (s) |
|---:|---:|---:|---:|---:|
| 0.85 | 1,200 | 1e-10 | 20 | 0.0222 |
| 0.85 | 20,000 | 1e-10 | 21 | 0.5937 |
| 0.95 | 1,200 | 1e-10 | 23 | 0.0258 |
| 0.95 | 20,000 | 1e-10 | 24 | 0.6977 |

Increasing the graph from 1,200 to 20,000 nodes, about **16.7x**, added only one iteration for each beta. However, wall time increased about **26.8x** at beta 0.85 and **27.0x** at beta 0.95. Iteration count is mainly controlled by beta, tolerance, and the graph's spectral structure, whereas the cost of each iteration grows with the number of nodes and edges that must be processed.

## A5 · Cost of a tighter tolerance

These measurements used beta 0.85 and 1,200 nodes.

| Tolerance | Iterations | Time (s) |
|---:|---:|---:|
| 1e-3 | 7 | 0.0092 |
| 1e-10 | 20 | 0.0222 |

Tightening the tolerance from `1e-3` to `1e-10` demanded seven additional decimal digits of precision and increased the iteration count by 13. In this experiment, each extra decimal digit cost approximately **13 / 7 = 1.86 additional iterations** on average. The tighter run also took about **2.4x** as long.

## A6 · Top-10 stability

The same ten pages remained in the top 10 for every tested beta, and the first six positions were unchanged. The first ordering change occurred at **beta 0.70**: `p00000` was seventh and `p00004` eighth at beta 0.50, but the two pages switched positions at beta 0.70 and remained in that order for beta 0.85, 0.95, and 0.99.

This result shows that the leading pages were robust on this graph, but the exact published ordering was still influenced by the chosen beta. A ranking should therefore report its beta and convergence settings rather than presenting the order as parameter-free.
