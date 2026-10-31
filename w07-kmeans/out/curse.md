# Task 2 — Curse of dimensionality

## Measurement method

Uniform points in [0, 1]^d. Each sampled pair contains two different point indices; pairs are sampled with replacement.
Minimum and maximum are sampled extremes, not the exact nearest/farthest distances among all possible pairs.
Each row is one timed run. Time includes point generation and distance sampling, but excludes file writing.

## Environment

```json
{
  "platform": "Windows-11-10.0.26200-SP0",
  "processor": "12th Gen Intel(R) Core(TM) i5-1240P",
  "python": "3.14.7",
  "logical_cpus": 16
}
```

Other running applications were not automatically inspected.
Historical rows retain their own machine and session metadata in curse.json.

## Measured table

| Session | n | d | Pairs | Min | Max | Mean | SD | Contrast | SD / mean | Mean / sqrt(d) | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 2 | 20000 | 0.0027 | 1.3220 | 0.5258 | 0.2489 | 487.2873 | 0.4734 | 0.3718 | 0.047 |
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 5 | 20000 | 0.0462 | 1.6964 | 0.8819 | 0.2472 | 35.7390 | 0.2803 | 0.3944 | 0.051 |
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 10 | 20000 | 0.4562 | 2.1636 | 1.2732 | 0.2466 | 3.7431 | 0.1937 | 0.4026 | 0.067 |
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 20 | 20000 | 0.8375 | 2.7531 | 1.8147 | 0.2438 | 2.2873 | 0.1344 | 0.4058 | 0.119 |
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 50 | 20000 | 1.9434 | 3.7299 | 2.8668 | 0.2366 | 0.9193 | 0.0825 | 0.4054 | 0.235 |
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 100 | 20000 | 3.2057 | 4.9089 | 4.0671 | 0.2413 | 0.5313 | 0.0593 | 0.4067 | 0.487 |
| 2026-10-31T10:56:13.250195+00:00 | 1000 | 200 | 20000 | 4.8709 | 6.7055 | 5.7745 | 0.2407 | 0.3767 | 0.0417 | 0.4083 | 0.847 |
| 2026-10-31T10:56:13.250195+00:00 | 250 | 100 | 20000 | 3.0592 | 4.9375 | 4.0813 | 0.2400 | 0.6140 | 0.0588 | 0.4081 | 0.400 |
| 2026-10-31T10:56:13.250195+00:00 | 2000 | 100 | 20000 | 3.1658 | 5.0459 | 4.0718 | 0.2421 | 0.5939 | 0.0595 | 0.4072 | 0.895 |

## A3: contrast thresholds

- n=250, seed=246, sampled pairs=20000:
  - First tested dimension with contrast < 1.0: d=100.
  - Contrast < 0.5 was not observed in the tested dimensions.
- n=1000, seed=246, sampled pairs=20000:
  - First tested dimension with contrast < 1.0: d=50.
  - First tested dimension with contrast < 0.5: d=200.
- n=2000, seed=246, sampled pairs=20000:
  - First tested dimension with contrast < 1.0: d=100.
  - Contrast < 0.5 was not observed in the tested dimensions.

These are first observed crossings on the tested grid, not exact thresholds. Sampled extremes may fluctuate.

## A4: growth of mean distance

For independent uniform coordinates, E[(X-Y)^2] = 1/6, so E[distance^2] = d/6. At high dimension, concentration suggests mean distance approximately sqrt(d/6), rather than linear growth in d.
The table reports mean / sqrt(d); compare it with 1/sqrt(6) = 0.4082. This is an asymptotic comparison, not an exact formula for mean distance at small d.

## A5: relative standard deviation

SD / mean measures concentration across the sampled distance distribution, while contrast depends on just its sampled minimum and maximum. Relative SD is usually more stable for describing typical concentration; contrast is useful for examining the observed range.
A small relative SD does not prove that every nearest-neighbor task is useless: structured data can differ from uniform points in a cube.

## A6: varying point count at a fixed dimension

- d=100, seed=246, sampled pairs=20000: n=250: contrast=0.6140, relative SD=0.0588; n=1000: contrast=0.5313, relative SD=0.0593; n=2000: contrast=0.5939, relative SD=0.0595.

Changing n changes the finite point cloud and the chance of resampling the same pair. However, this experiment keeps the sampled pair count fixed instead of examining all n(n-1)/2 pairs. A monotonic increase in sampled contrast with n is therefore not guaranteed, and a single run does not isolate a systematic n effect from sampling variation.

## A7: runtime

- Largest dimension in the current invocation: d=200, n=1000, pairs=20000; 0.847 seconds.
- Slowest run in the current invocation: d=100, n=2000; 0.895 seconds.

## A8: connection to Week 3 Jaccard LSH

This experiment measures Euclidean distances between uniform dense vectors. Week 3 uses Jaccard similarity between shingle sets, so this result does not directly establish that Jaccard LSH fails.
MinHash collision probability tracks Jaccard similarity. LSH is useful when relevant and irrelevant pairs have different similarities; if those similarities themselves concentrate, distinguishing pairs becomes difficult. The relevant similarity distribution must be measured instead of transferring a Euclidean result unchanged.
