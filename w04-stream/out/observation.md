# Week 4 · Observations

## Task 1

- A Bloom filter has no false negatives because insertion sets every bit checked by a later query, and this implementation never clears bits. Its predicted false-positive rate was **0.860%**, close to the measured **0.880%**.
- The FM sketch used 64 registers with stochastic/geometric averaging and estimated **27,258** for a true count of **19,953** (**1.37x**). Median (**1.64x**) and grouped medians (**1.39x**) also passed, while the arithmetic mean (**3.85x**) was too sensitive to large outliers.
- Reservoir sampling is correct at `j = rng.randrange(i + 1)` followed by replacement only when `j < k`; therefore each arriving item has probability `k / (i + 1)` of entering the fixed-size sample without knowing the stream length.

## Task 2

- Exact counting became unpleasant at **6,400,000** items: it took **29.14 s** and peaked at **188.3 MB**. Runtime became inconvenient before RAM was exhausted on the 15.6 GB machine.
- Across a 64x input range, exact memory grew about **48.3x** (approximately O(n)), whereas the fixed-register FM sketch stayed at roughly **0.00–0.01 MB** (O(1)); its accuracy ratios varied non-monotonically from **0.86x to 1.39x**.
- Factor-of-two accuracy is adequate for approximate traffic or capacity trends, but not for billing, compliance, payments, or exact quota enforcement.

## Task 3

- With 80,000 bits and 8,000 inserted items, the optimal number of hashes is `k = (m/n) ln 2 = 10 ln 2 = 6.93`, so I used **7 hash functions**.
- The theoretical false-positive floor is about **0.819%**; the measured result was **0.832%** (1,664 false positives), close to the floor and far below the 9.511% baseline, with zero false negatives and the same memory budget.
- If `n` is unknown, I would size from an expected capacity, monitor saturation, and rotate or grow scalable Bloom-filter layers. Underestimating `n` raises false positives sharply, while overestimating it wastes bits.
