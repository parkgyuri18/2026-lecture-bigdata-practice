#!/usr/bin/env python3
"""Week 4 · Task 1 — Answer questions about a stream you cannot store.

Textbook §4.3 (sampling), §4.4 (Bloom filter), §4.5 (Flajolet-Martin).

The premise of the whole chapter: the stream is longer than your memory, it
goes past once, and you still have to answer. Every method here trades an exact
answer for a bounded amount of space, and the job is to know exactly what you
traded.

You build three, and the harness checks each against the truth it is
approximating.

    python3 task1_sketches.py --verify
"""
import argparse
import hashlib
import math
import random
import zlib


def _key_from_seed(seed):
    """Return a fixed-size BLAKE2 key for any seed value."""
    return hashlib.blake2b(
        str(seed).encode("utf-8"),
        digest_size=16
    ).digest()


def _hash_pair(item, key):
    """Return two deterministic 64-bit hashes for double hashing."""
    digest = hashlib.blake2b(
        repr(item).encode("utf-8"),
        digest_size=16,
        key=key,
    ).digest()

    first = int.from_bytes(
        digest[:8],
        "big"
    )

    second = (
        int.from_bytes(
            digest[8:],
            "big"
        )
        | 1
    )

    return first, second


class BloomFilter:
    """Membership, with one-sided error.

    A Bloom filter never says "no" about something you inserted. It sometimes
    says "yes" about something you did not. That asymmetry is the entire design
    and it is why it is useful for "have I seen this before" and useless for
    "is this definitely in the set".

    `m` bits, `k` hash functions.
    """

    def __init__(self, m, k, seed=246):
        if m <= 0:
            raise ValueError(
                "m must be positive"
            )

        if k <= 0:
            raise ValueError(
                "k must be positive"
            )

        self.m = m
        self.k = k
        self.seed = seed

        self.bits = bytearray(
            (m + 7) // 8
        )

        self._key = _key_from_seed(
            seed
        )

    def _indices(self, item):
        first, second = _hash_pair(
            item,
            self._key
        )

        for i in range(self.k):
            yield (
                first + i * second
            ) % self.m

    def add(self, item):
        for index in self._indices(
            item
        ):
            byte_index, bit_index = divmod(
                index,
                8
            )

            self.bits[byte_index] |= (
                1 << bit_index
            )

    def __contains__(self, item):
        for index in self._indices(
            item
        ):
            byte_index, bit_index = divmod(
                index,
                8
            )

            if not (
                self.bits[byte_index]
                & (1 << bit_index)
            ):
                return False

        return True

    def expected_fp_rate(self, n_inserted):
        """Return the theoretical false-positive rate."""
        if n_inserted < 0:
            raise ValueError(
                "n_inserted must not be negative"
            )

        return (
            1.0
            - math.exp(
                -self.k
                * n_inserted
                / self.m
            )
        ) ** self.k


def flajolet_martin(stream, n_hashes=64, seed=246):
    """Estimate the number of distinct items in one stream pass.

    Stochastic averaging divides the hash space into fixed registers.
    Each item updates only one register, so processing takes O(n) time
    instead of O(n * n_hashes).

    The stream is never stored.
    """
    if n_hashes <= 0:
        raise ValueError(
            "n_hashes must be positive"
        )

    maxima = [0] * n_hashes
    item_count = 0

    # If n_hashes is a power of two, the lower hash bits can choose
    # the register efficiently without using modulo.
    power_of_two = (
        n_hashes
        & (n_hashes - 1)
    ) == 0

    bucket_bits = (
        n_hashes.bit_length() - 1
        if power_of_two
        else 0
    )

    bucket_mask = n_hashes - 1

    for item in stream:
        item_count += 1

        # CRC32 is deterministic and implemented in C.
        # It is much faster than creating a cryptographic BLAKE2 hash
        # for every one of millions of stream items.
        hashed = zlib.crc32(
            str(item).encode("utf-8"),
            seed & 0xFFFFFFFF,
        )

        if power_of_two:
            # Lower bits choose one of the fixed registers.
            bucket = (
                hashed & bucket_mask
            )

            # Remaining bits provide the trailing-zero observation.
            remaining = (
                hashed >> bucket_bits
            )

            remaining_bits = (
                32 - bucket_bits
            )

        else:
            bucket = (
                hashed % n_hashes
            )

            remaining = (
                hashed // n_hashes
            )

            remaining_bits = 32

        if remaining == 0:
            trailing_zeros = remaining_bits
        else:
            trailing_zeros = (
                remaining
                & -remaining
            ).bit_length() - 1

        if (
            trailing_zeros
            > maxima[bucket]
        ):
            maxima[bucket] = (
                trailing_zeros
            )

    if item_count == 0:
        return 0.0

    # The arithmetic mean of R is equivalent to using the geometric
    # mean of the individual 2^R estimates.
    average_r = (
        sum(maxima)
        / n_hashes
    )

    # Each register observes approximately 1/n_hashes of the stream.
    # Multiply the register estimate by n_hashes to estimate the
    # complete number of distinct items.
    return float(
        n_hashes
        * (2.0 ** average_r)
    )


def reservoir_sample(stream, k, seed=246):
    """Keep k uniformly selected items from an unknown-length stream."""
    if k < 0:
        raise ValueError(
            "k must not be negative"
        )

    if k == 0:
        return []

    rng = random.Random(seed)
    sample = []

    for i, item in enumerate(stream):
        # Initially store the first k items.
        if i < k:
            sample.append(item)
            continue

        # For the (i + 1)-th item, generate a random position
        # from 0 through i.
        replacement_index = rng.randrange(
            i + 1
        )

        # Replace one reservoir position with probability k/(i + 1).
        if replacement_index < k:
            sample[
                replacement_index
            ] = item

    return sample


# ------------------------------------------------------------------- harness
def verify():
    fails = 0
    rng = random.Random(246)

    def check(label, ok, detail=""):
        nonlocal fails

        print(
            f"  {'ok  ' if ok else 'FAIL'}  "
            f"{label:<46} {detail}"
        )

        fails += not ok

    # --- Bloom: no false negatives, ever
    try:
        bf = BloomFilter(
            m=8192,
            k=5
        )

    except NotImplementedError:
        print(
            "  BloomFilter is still a stub"
        )
        return 1

    inserted = [
        f"item-{i}"
        for i in range(800)
    ]

    for x in inserted:
        bf.add(x)

    check(
        "no false negatives",
        all(
            x in bf
            for x in inserted
        )
    )

    absent = [
        f"other-{i}"
        for i in range(20_000)
    ]

    fp = (
        sum(
            1
            for x in absent
            if x in bf
        )
        / len(absent)
    )

    predicted = bf.expected_fp_rate(
        len(inserted)
    )

    close = (
        abs(fp - predicted)
        < max(
            0.02,
            predicted * 0.5
        )
    )

    check(
        "measured false-positive rate matches theory",
        close,
        (
            f"measured {fp:.3%}, "
            f"predicted {predicted:.3%}"
        ),
    )

    # --- Flajolet-Martin
    try:
        distinct = 20_000

        stream = [
            f"k{rng.randrange(distinct)}"
            for _ in range(120_000)
        ]

        est = flajolet_martin(
            stream
        )

    except NotImplementedError:
        print(
            "  flajolet_martin is still a stub"
        )
        return 1

    true_distinct = len(
        set(stream)
    )

    ratio = (
        est
        / true_distinct
    )

    check(
        "distinct estimate within a factor of 2",
        0.5 <= ratio <= 2.0,
        (
            f"estimated {est:,.0f}, "
            f"true {true_distinct:,} "
            f"({ratio:.2f}x)"
        ),
    )

    # --- Reservoir sampling
    try:
        counts = [0] * 20
        trials = 4000

        for t in range(trials):
            sample = reservoir_sample(
                range(20),
                5,
                seed=t
            )

            for item in sample:
                counts[item] += 1

    except NotImplementedError:
        print(
            "  reservoir_sample is still a stub"
        )
        return 1

    expected = (
        trials
        * 5
        / 20
    )

    spread = (
        max(counts)
        - min(counts)
    ) / expected

    check(
        "reservoir is uniform across items",
        spread < 0.15,
        (
            f"spread {spread:.1%} "
            f"around {expected:.0f}"
        ),
    )

    print(
        f"\n  "
        f"{'all ok' if not fails else str(fails) + ' failed'}"
    )

    return (
        1
        if fails
        else 0
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--verify",
        action="store_true"
    )

    args = parser.parse_args()

    raise SystemExit(
        verify()
        if args.verify
        else parser.print_help()
    )