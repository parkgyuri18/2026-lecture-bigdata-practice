# Task 2 Crossover Results

## Machine

| Item | Value |
|---|---|
| Platform | Windows 11 (10.0.26200) |
| Processor | Intel64 Family 6 Model 181 Stepping 0, GenuineIntel |
| Python | 3.14.7 |
| RAM | 15.5 GB |

## Measurements

| Documents | Brute time (s) | Brute comparisons | Brute peak memory | LSH time (s) | LSH comparisons | LSH peak memory |
|---:|---:|---:|---:|---:|---:|---:|
| 250 | 0.19 | 31,125 | 7,880 B | 3.32 | 15 | 1,393,088 B |
| 500 | 0.63 | 124,750 | 9,352 B | 6.22 | 29 | 2,771,136 B |
| 1,000 | 2.24 | 499,500 | 9,512 B | 12.06 | 61 | 5,546,048 B |
| 2,000 | 9.31 | 1,999,000 | 18,792 B | 24.02 | 120 | 11,104,696 B |
| 3,000 | 27.58 | 4,498,500 | 33,960 B | 61.53 | 185 | 16,823,696 B |
| 3,500 | 36.17 | 6,123,250 | 37,288 B | 42.13 | 207 | 19,591,784 B |
| 4,000 | 53.79 | 7,998,000 | 40,840 B | 48.45 | 238 | 22,369,056 B |

## Quadratic check

For brute force, doubling `n` from 250 to 500, 500 to 1,000, and 1,000 to
2,000 increased the measured time by about 3.32x, 3.57x, and 4.15x. The exact
comparison counts grow from 31,125 to 124,750 to 499,500 to 1,999,000, which is
approximately 4x per doubling and agrees with the quadratic formula
`n(n-1)/2`.

## Crossover

At 3,500 documents, brute force was still faster (36.17 s versus 42.13 s).
At 4,000 documents, LSH became faster (48.45 s versus 53.79 s). Therefore the
observed crossover is between 3,500 and 4,000 documents.

LSH loses at small `n` because it must first build 160-value MinHash signatures
for every document and organize them into 40 bands and buckets. This setup cost
is roughly linear, but it is larger than brute-force comparison work on small
inputs. At 4,000 documents, peak measured memory was 40,840 bytes for brute
force and 22,369,056 bytes (about 21.3 MiB) for LSH. The run became unpleasant
at 3,000 documents, where LSH took 61.53 seconds.
