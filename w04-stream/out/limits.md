# Task 2 · Exact Distinct Counting Limits

## Test environment

- **CPU:** 12th Gen Intel(R) Core(TM) i5-1240P
- **RAM:** 15.6 GB
- **Python:** 3.14.7
- **Programs open during the run:** Visual Studio Code, KakaoTalk, File Explorer, Chrome, and ChatGPT

## Measurements

| Stream size (n) | True distinct | Exact time | Exact peak memory | FM time | FM peak memory | FM / exact |
|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 36,702 | 0.28 s | 3.9 MB | 0.70 s | 0.01 MB | 1.29x |
| 200,000 | 73,410 | 0.60 s | 5.8 MB | 1.50 s | 0.00 MB | 1.08x |
| 400,000 | 146,970 | 1.20 s | 11.6 MB | 2.68 s | 0.00 MB | 1.39x |
| 1,600,000 | 587,625 | 4.18 s | 46.6 MB | 10.82 s | 0.00 MB | 0.86x |
| 6,400,000 | 2,349,909 | 29.14 s | 188.3 MB | 54.39 s | 0.01 MB | 1.28x |

The `0.00 MB` FM values are rounded display values, not literally zero memory. The sketch keeps a fixed number of registers, so its memory is very small and does not grow with the stream size.

## Where exact counting became unpleasant

Exact counting first became inconvenient at **n = 6,400,000**: it took **29.14 seconds** and used **188.3 MB** of peak memory. Time was the first practical problem on this machine; 188.3 MB was noticeable but did not approach the 15.6 GB RAM limit. Exact counting was still faster than this Python FM implementation, but its set continued to grow while FM retained nearly constant memory.

## Growth rates

The input grew by **64x** from 100,000 to 6,400,000. Over the same range, exact peak memory grew from 3.9 MB to 188.3 MB, about **48.3x**, which is consistent with approximately linear, **O(n)** growth. Exact time grew about **104.1x**; resizing, hashing, cache effects, and memory tracing make the largest run slower than an ideal linear trend.

FM peak memory stayed between the rounded values 0.00 and 0.01 MB, so it is **O(1)** for a fixed register count. FM time grew from 0.70 seconds to 54.39 seconds, about **77.7x**, which is broadly linear because every stream item must still be processed once.

## Accuracy trend and acceptable use

The FM/exact ratios were **1.29, 1.08, 1.39, 0.86, and 1.28**. All estimates were within the required factor of two, but accuracy did not improve monotonically as the stream grew; sketch error varies with the hash pattern and register values.

A factor-of-two estimate can be useful for approximate traffic monitoring, capacity planning, or deciding whether a trend is growing. It is not acceptable for billing, compliance reports, payments, or enforcing exact unique-user quotas, where the precise count changes the outcome.
