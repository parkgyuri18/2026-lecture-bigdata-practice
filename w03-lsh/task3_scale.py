#!/usr/bin/env python3
"""Week 3 · Task 3 — Find the same pairs without comparing everything.

Textbook §3.4.

`BruteForce` compares every pair. On 3,000 documents that is 4.5 million
comparisons and it is completely correct. On 3 million documents it is 4.5
trillion and it is completely useless.

Beat it. Find the same near-duplicate pairs while making far fewer comparisons.

    python3 bench.py
    python3 bench.py --yours

The harness counts every call you make to `similarity()`. That is your score.
It also checks **recall** - which of the truly similar pairs you found. Skipping
comparisons is easy; skipping comparisons without losing the pairs is the task.
"""


class BruteForce:
    """Correct, and quadratic."""

    def __init__(self, threshold):
        self.threshold = threshold

    def find(self, docs, similarity):
        """docs is [set_of_shingles, ...]. Return {(i, j), ...} with i < j."""
        out = set()
        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                if similarity(docs[i], docs[j]) >= self.threshold:
                    out.add((i, j))
        return out


class YourFinder:
    """Your near-duplicate finder.

        __init__(threshold)
        find(docs, similarity) -> {(i, j), ...}

    `similarity(a, b)` is the only way to compare two documents, and every call
    is counted. Everything else - signatures, banding, bucketing - is free, in
    the sense that the harness does not charge you for it. That is deliberate:
    it is also roughly true at scale, where the comparison is the expensive
    part and the hashing is linear.

    Two knobs decide everything:

        the number of hashes in a signature
        how many bands you split it into

    §3.4.2 gives you the relationship between those and the probability that a
    pair at similarity s becomes a candidate. It is an S-curve, and where its
    step sits is something you choose. Choose it on purpose and be able to say
    why in observation.md - a threshold of 0.8 does not mean bands should be
    anything in particular until you have done the arithmetic.

    You may reuse your Task 1 code.
    """

    def __init__(self, threshold):
        self.threshold = threshold

        # 160 signature rows split into 40 bands of 4 rows each.
        # The S-curve step is (1 / 40) ** (1 / 4) = 0.398.
        # At s = 0.6, the candidate probability is
        # 1 - (1 - 0.6 ** 4) ** 40 = 0.9961.
        self.num_hashes = 160
        self.bands = 40
        self.rows_per_band = self.num_hashes // self.bands

        # Fixed coefficients make every run reproducible.  The prime is larger
        # than the shingle IDs used by the benchmark.
        self.prime = 4_294_967_311
        self.coefficients = []
        state = 24_680
        for _ in range(self.num_hashes):
            state = (1_103_515_245 * state + 12_345) & 0x7fffffff
            a = state + 1
            state = (1_103_515_245 * state + 12_345) & 0x7fffffff
            b = state
            self.coefficients.append((a, b))

    def find(self, docs, similarity):
        if not docs:
            return set()

        # Build one MinHash signature for each document.
        signatures = []
        for doc in docs:
            if not doc:
                signatures.append([self.prime] * self.num_hashes)
                continue

            signature = []
            for a, b in self.coefficients:
                signature.append(
                    min((a * shingle + b) % self.prime for shingle in doc)
                )
            signatures.append(signature)

        # Documents that agree in any band become candidate pairs.
        candidates = set()
        for band in range(self.bands):
            start = band * self.rows_per_band
            end = start + self.rows_per_band
            buckets = {}

            for doc_id, signature in enumerate(signatures):
                key = tuple(signature[start:end])
                bucket = buckets.setdefault(key, [])

                for other_id in bucket:
                    candidates.add((other_id, doc_id))

                bucket.append(doc_id)

        # Only exact comparisons are counted by the harness.
        found = set()
        for i, j in candidates:
            if similarity(docs[i], docs[j]) >= self.threshold:
                found.add((i, j))

        return found
