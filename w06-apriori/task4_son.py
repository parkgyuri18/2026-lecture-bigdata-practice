#!/usr/bin/env python3
"""Week 6 · Task 4 — SON frequent-pair mining.

실행:
    python3 task4_son.py
    python3 task4_son.py --chunks 4
    python3 task4_son.py --spark
"""

import argparse
import time
from collections import Counter
from itertools import combinations


def son_pass_one(chunks, support, total_baskets):
    """각 청크의 빈발 쌍을 합쳐 후보 집합을 만든다."""
    from task1_apriori import frequent_pairs

    candidates = set()

    if total_baskets == 0:
        return candidates

    for chunk in chunks:
        if not chunk:
            continue

        # ceil(support * 청크 크기 / 전체 바구니 수)
        scaled_support = (
            support * len(chunk) + total_baskets - 1
        ) // total_baskets

        local_pairs = frequent_pairs(chunk, scaled_support)
        candidates.update(local_pairs)

    return candidates


def son_pass_two(baskets, candidates, support):
    """전체 데이터에서 후보 쌍만 세고 실제 빈발 쌍을 반환한다."""
    counts = Counter()

    for basket in baskets:
        for pair in combinations(set(basket), 2):
            key = frozenset(pair)

            if key in candidates:
                counts[key] += 1

    return {
        pair: count
        for pair, count in counts.items()
        if count >= support
    }


def chunked(baskets, n_chunks):
    """바구니를 최대 n_chunks개의 청크로 나눈다."""
    if n_chunks < 1:
        raise ValueError("n_chunks must be at least 1")

    size = max(1, (len(baskets) + n_chunks - 1) // n_chunks)

    return [
        baskets[i:i + size]
        for i in range(0, len(baskets), size)
    ]


def spark_son(baskets, support, n_chunks):
    """과제에서 제공한 Spark 비교 구현."""
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName("w06")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    try:
        sc = spark.sparkContext
        sc.setLogLevel("ERROR")

        total = len(baskets)

        if total == 0:
            return {}, 0

        rdd = (
            sc.parallelize(baskets, n_chunks)
            .map(lambda b: sorted(b))
            .cache()
        )

        def local_frequent(it):
            chunk = list(it)

            if not chunk:
                return []

            scaled = support * len(chunk) / total
            counts = {}

            for basket in chunk:
                for pair in combinations(basket, 2):
                    counts[pair] = counts.get(pair, 0) + 1

            return [
                pair
                for pair, count in counts.items()
                if count >= scaled
            ]

        candidates = set(
            rdd.mapPartitions(local_frequent)
            .distinct()
            .collect()
        )

        bc = sc.broadcast(candidates)

        def count_candidates(it):
            counts = {}

            for basket in it:
                items = set(basket)

                for pair in bc.value:
                    if items.issuperset(pair):
                        counts[pair] = counts.get(pair, 0) + 1

            return counts.items()

        final = (
            rdd.mapPartitions(count_candidates)
            .reduceByKey(lambda a, b: a + b)
            .filter(lambda kv: kv[1] >= support)
            .collectAsMap()
        )

        return (
            {frozenset(pair): count for pair, count in final.items()},
            len(candidates),
        )

    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spark", action="store_true")
    parser.add_argument("--chunks", type=int, default=8)
    args = parser.parse_args()

    if args.chunks < 1:
        parser.error("--chunks must be at least 1")

    import bench
    from task3_pcy import PlainApriori

    baskets = bench.build()
    support = bench.SUPPORT

    print(
        f"\n  {len(baskets):,} baskets, support {support}, "
        f"{args.chunks} chunks\n"
    )

    start = time.perf_counter()
    truth = PlainApriori(support).run(baskets)
    baseline_seconds = time.perf_counter() - start

    print(
        f"  task 3 baseline   {baseline_seconds:7.2f}s   "
        f"pairs {len(truth):>6,}"
    )

    start = time.perf_counter()

    candidates = son_pass_one(
        chunked(baskets, args.chunks),
        support,
        len(baskets),
    )

    found = son_pass_two(baskets, candidates, support)
    son_seconds = time.perf_counter() - start

    missing = len(set(truth) - set(found))
    extra = len(set(found) - set(truth))

    print(
        f"  your SON          {son_seconds:7.2f}s   "
        f"pairs {len(found):>6,}   "
        f"candidates {len(candidates):>7,}   "
        f"missing {missing}, extra {extra}"
    )

    # 쌍의 종류뿐 아니라 각 쌍의 support도 검증한다.
    correct = found == truth

    if correct:
        print("    PASS: frequent pairs and support counts match.")
    else:
        print("    FAIL: frequent pairs or support counts differ.")

    if args.spark:
        try:
            start = time.perf_counter()

            spark_pairs, candidate_count = spark_son(
                baskets,
                support,
                args.chunks,
            )

            spark_seconds = time.perf_counter() - start
            spark_missing = len(set(truth) - set(spark_pairs))
            spark_extra = len(set(spark_pairs) - set(truth))

            print(
                f"  spark SON         {spark_seconds:7.2f}s   "
                f"pairs {len(spark_pairs):>6,}   "
                f"candidates {candidate_count:>7,}   "
                f"missing {spark_missing}, extra {spark_extra}"
            )

            if spark_pairs == truth:
                print("    PASS: Spark pairs and support counts match.")
            else:
                print("    FAIL: Spark result differs from baseline.")
                correct = False

        except Exception as error:
            print(
                f"  spark SON         did not run: "
                f"{type(error).__name__}: {error}"
            )
            print(
                "  Record this in observation.md. "
                "Spark execution is optional."
            )

    print()
    return 0 if correct else 1


if __name__ == "__main__":
    raise SystemExit(main())