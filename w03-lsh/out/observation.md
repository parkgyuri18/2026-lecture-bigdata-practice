## Task 1

The row loop is outermost so each matrix row is read once while every matching column is updated; scanning once per column would repeat the data pass and would not scale as a streaming algorithm. I require the signature length to divide evenly by the band count and raise `ValueError` otherwise. S1-S4 is estimated as 1.0 instead of the true 2/3 with only two hashes; more hashes would reduce variance at the cost of additional time and memory.

## Task 2

On Windows 11 with an Intel64 Family 6 Model 154 CPU and Python 3.14.7, no runtime crossover appeared between 125 and 2,000 documents: brute force remained faster because LSH paid to build 160-value signatures and 40 bands before comparing candidates. Doubling `n` changed brute-force time by about 3.83x, 4.00x, 3.94x, and 4.68x, which supports quadratic growth. The experiment became unpleasant at `n = 2,000`, where LSH took 79.91 seconds and used about 12.9 MiB peak memory; installed RAM and background activity were not captured by the provided harness and must be recorded from Windows before submission.

## Task 3

I used 160 MinHash values split into 40 bands with 4 rows per band. The S-curve step is `(1/40)^(1/4) = 0.398`, and at similarity 0.6 the candidate probability is `1-(1-0.6^4)^40 = 0.9961`, which protects recall while keeping the candidate set small. This achieved 100.0% recall with 123 comparisons; moving the step above the threshold using 20 bands of 8 rows (`(1/20)^(1/8) = 0.688`) reduced recall to 86.0%. At millions of documents, the time and memory required to build and store 160-value signatures would make the harness's assumption that hashing is free increasingly unrealistic.
