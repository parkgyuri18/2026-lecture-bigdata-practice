#!/usr/bin/env python3
"""Week 4 · Task 3 — Same memory, fewer mistakes.

Textbook §4.4 (Bloom filters), §4.5 (counting distinct).

`NaiveFilter` is a membership filter in a fixed number of bits. It works. It
also makes far more mistakes than it has to with the memory it was given, and
it does so for a reason you can find by reading §4.4.2 and doing one derivative.

You get **exactly the same number of bits**. Make fewer mistakes.

    python3 bench.py
    python3 bench.py --yours

The rule that makes this interesting: a false negative is not allowed. Ever.
The whole point of this structure is that "no" means no. A filter that gets a
better score by occasionally forgetting something it was given has not improved
anything, it has broken the contract.
"""
import hashlib
import math


class NaiveFilter:
    """One hash function, and the bits it was given."""

    def __init__(self, n_bits, seed=246):
        self.n_bits = n_bits
        self.seed = seed
        self.bits = bytearray(n_bits)

    def _index(self, item):
        d = hashlib.blake2b(
            str(item).encode(),
            digest_size=8,
            key=str(self.seed).encode(),
        ).digest()

        return int.from_bytes(
            d,
            "big"
        ) % self.n_bits

    def add(self, item):
        self.bits[
            self._index(item)
        ] = 1

    def __contains__(self, item):
        return bool(
            self.bits[
                self._index(item)
            ]
        )

    def memory_bits(self):
        return self.n_bits


class YourFilter:
    """A Bloom filter using the optimal number of hash functions.

    The harness inserts 8,000 items into 80,000 bits, so m/n = 10. The Bloom
    filter false-positive formula is minimised at

        k = (m / n) * ln(2) = 10 * ln(2) = 6.93

    Therefore this implementation uses seven hash functions. The bit array is
    packed into bytes, so the 80,000-bit budget occupies exactly 10,000 bytes.
    """

    BITS_PER_EXPECTED_ITEM = 10

    def __init__(self, n_bits, seed=246):
        if n_bits <= 0:
            raise ValueError(
                "n_bits must be positive"
            )

        self.n_bits = n_bits
        self.seed = seed

        # Optimal number of Bloom-filter hash functions:
        # k = (m / n) * ln(2)
        # k = 10 * ln(2) = 6.93, so use 7.
        self.n_hashes = max(
            1,
            round(
                self.BITS_PER_EXPECTED_ITEM
                * math.log(2)
            ),
        )

        # Pack eight filter bits into each byte.
        #
        # 80,000 bits / 8 = 10,000 bytes.
        self.bits = bytearray(
            (n_bits + 7) // 8
        )

        # Create a fixed-size deterministic key from the seed.
        self._key = hashlib.blake2b(
            str(seed).encode("utf-8"),
            digest_size=16,
        ).digest()

    def _indices(self, item):
        """Generate seven deterministic positions using double hashing."""

        digest = hashlib.blake2b(
            str(item).encode("utf-8"),
            digest_size=16,
            key=self._key,
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

        for i in range(
            self.n_hashes
        ):
            yield (
                first + i * second
            ) % self.n_bits

    def add(self, item):
        """Set every Bloom-filter bit belonging to the item."""

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
        """Return True when all seven required bits are set."""

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

    def memory_bits(self):
        """Report the complete size of the packed bit array in bits."""

        return len(self.bits) * 8