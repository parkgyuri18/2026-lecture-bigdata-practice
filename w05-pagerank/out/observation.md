# Week 5 Observations

## Task 1
Without the fix, rank at a dead end disappears because there is no outgoing link; I redistributed that dangling rank uniformly across all nodes instead.
Teleportation fixes both dead ends and spider traps by continually returning probability mass to the whole graph: with probability `beta` the surfer follows a link, and with probability `1 - beta` jumps to a uniformly chosen page.

## Task 2
As `beta` approached 1, convergence required more iterations (`14` at `0.50` versus `24` at `0.99`), while increasing the graph from 1,200 to 20,000 nodes barely changed the iteration count but greatly increased wall time because every iteration processed more nodes and edges.
The top-10 order first changed at `beta = 0.70` (`p00004` moved above `p00000`), although the top three pages remained `p00009`, `p00001`, and `p00006`; therefore, the selected beta can affect a published ranking and should be reported.

## Task 3
Instead of storing the dense `n × n` transition matrix, I kept an adjacency list and rank vectors, reducing storage from `O(n²)` to about `O(n + E)` (`1,440,000` floats versus `2,400`), while the measured implementation was `110.5×` faster and used `600.0×` less memory.
The teleport and dead-end terms only require one scalar base contribution applied to every entry of the next rank vector, not a dense matrix; the worst per-node difference was `1.18e-15`, caused only by floating-point accumulation order.

## Task 4 (Optional)
At 50,000 nodes and 376,379 edges, the single-process version took `2.17 s` with `14.3 MB` peak traced memory, while Spark took `135.47 s`; both ranked node `147` first, but Spark was `62.4×` slower because its startup, worker, serialization, join, and shuffle overhead dominated at this scale.
The Spark ranks summed to `0.9959` because nodes receiving no incoming contribution disappeared after `reduceByKey` and therefore missed the teleport term; a complete version would retain every node and add the teleport and dangling-rank contributions to all of them.
Only the 50,000-node comparison was measured, so the single-process limit and a multi-size memory curve were not determined; Spark becomes appropriate when a graph no longer fits in one machine's memory and can be partitioned across multiple workers.
