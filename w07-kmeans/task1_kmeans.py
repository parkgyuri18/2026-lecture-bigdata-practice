#!/usr/bin/env python3
"""Task 1: k-means and k-means++ initialization.

실행:
    python3 task1_kmeans.py --verify
"""

import argparse
import math
import random


BLOBS = [
    (0.0, 0.0), (0.2, 0.1), (0.1, 0.2),
    (8.0, 8.0), (8.2, 8.1), (8.1, 8.2),
    (0.0, 8.0), (0.2, 8.1), (0.1, 8.2),
]


def euclidean(a, b):
    """임의 차원의 유클리드 거리."""
    if len(a) != len(b):
        raise ValueError("Points must have the same dimension.")

    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def assign(points, centroids):
    """가장 가까운 중심에 배정한다. 동률이면 낮은 인덱스."""
    if not centroids:
        raise ValueError("At least one centroid is required.")

    labels = []

    for point in points:
        best_index = 0
        best_distance = euclidean(point, centroids[0])

        for index in range(1, len(centroids)):
            value = euclidean(point, centroids[index])

            if value < best_distance:
                best_distance = value
                best_index = index

        labels.append(best_index)

    return labels


def update(points, labels, k, previous=None):
    """각 클러스터의 평균을 계산한다.

    kmeans()에서는 previous를 전달해 빈 클러스터의 기존 중심을 유지한다.
    기존 3인자 인터페이스로 직접 호출하면 빈 클러스터는 첫 점으로 대체한다.
    """
    if not points:
        raise ValueError("points must not be empty.")

    if len(points) != len(labels):
        raise ValueError("One label is required for each point.")

    dimension = len(points[0])
    sums = [[0.0] * dimension for _ in range(k)]
    counts = [0] * k

    for point, label in zip(points, labels):
        counts[label] += 1

        for axis, value in enumerate(point):
            sums[label][axis] += value

    centroids = []

    for index in range(k):
        if counts[index]:
            centroids.append(
                tuple(value / counts[index] for value in sums[index])
            )
        elif previous is not None:
            centroids.append(tuple(previous[index]))
        else:
            centroids.append(tuple(points[0]))

    return centroids


def sse_of(points, labels, centroids):
    """각 점과 배정된 중심 사이 거리의 제곱합."""
    return sum(
        sum(
            (value - center_value) ** 2
            for value, center_value in zip(point, centroids[label])
        )
        for point, label in zip(points, labels)
    )


def _initialize(points, k, init, rng):
    if init == "random":
        return [tuple(point) for point in rng.sample(points, k)]

    if init != "++":
        raise ValueError("init must be 'random' or '++'.")

    first = rng.randrange(len(points))
    chosen = {first}
    centroids = [tuple(points[first])]

    nearest_squared = [
        sum((x - y) ** 2 for x, y in zip(point, centroids[0]))
        for point in points
    ]

    while len(centroids) < k:
        total = sum(nearest_squared)

        if total == 0:
            # 모든 점이 이미 선택한 중심과 같은 위치인 경우.
            remaining = [
                index
                for index in range(len(points))
                if index not in chosen
            ]
            selected = rng.choice(remaining)
        else:
            target = rng.random() * total
            cumulative = 0.0
            selected = None

            for index, weight in enumerate(nearest_squared):
                cumulative += weight

                if weight > 0 and target < cumulative:
                    selected = index
                    break

            if selected is None:
                selected = max(
                    range(len(points)),
                    key=lambda index: nearest_squared[index],
                )

        chosen.add(selected)
        center = tuple(points[selected])
        centroids.append(center)

        for index, point in enumerate(points):
            squared = sum(
                (x - y) ** 2 for x, y in zip(point, center)
            )
            nearest_squared[index] = min(
                nearest_squared[index], squared
            )

    return centroids


def kmeans(points, k, init="random", seed=246, max_iter=100):
    """(labels, centroids, sse)를 반환한다."""
    points = [tuple(point) for point in points]
    kmeans.iterations = 0

    if not points:
        raise ValueError("points must not be empty.")

    if not 1 <= k <= len(points):
        raise ValueError("k must be between 1 and len(points).")

    if max_iter < 1:
        raise ValueError("max_iter must be positive.")

    dimension = len(points[0])

    if any(len(point) != dimension for point in points):
        raise ValueError("All points must have the same dimension.")

    rng = random.Random(seed)
    centroids = _initialize(points, k, init, rng)
    labels = None

    for iteration in range(1, max_iter + 1):
        new_labels = assign(points, centroids)
        new_centroids = update(
            points, new_labels, k, previous=centroids
        )

        unchanged = new_labels == labels
        labels = new_labels
        centroids = new_centroids
        kmeans.iterations = iteration

        if unchanged:
            break

    return labels, centroids, sse_of(points, labels, centroids)


kmeans.iterations = 0


def verify():
    fails = 0

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<50} {detail}")
        fails += not ok

    check(
        "distance in 2d",
        abs(euclidean((0, 0), (3, 4)) - 5) < 1e-9,
    )
    check(
        "distance in 5d",
        abs(euclidean((0,) * 5, (1,) * 5) - math.sqrt(5)) < 1e-9,
    )

    labels, centroids, sse = kmeans(
        BLOBS, 3, init="++", seed=1
    )

    groups = {}

    for point, label in zip(BLOBS, labels):
        groups.setdefault(label, []).append(point)

    sizes = sorted(len(group) for group in groups.values())

    check("three clusters of three", sizes == [3, 3, 3], sizes)

    check(
        "the three blobs were recovered",
        all(
            max(point[0] for point in group)
            - min(point[0] for point in group) < 1
            and
            max(point[1] for point in group)
            - min(point[1] for point in group) < 1
            for group in groups.values()
        ),
    )

    check(
        "sse is small when clusters are right",
        sse < 1.0,
        f"sse {sse:.4f}",
    )

    randoms = [
        kmeans(BLOBS, 3, init="random", seed=seed)[2]
        for seed in range(40)
    ]
    plusplus = [
        kmeans(BLOBS, 3, init="++", seed=seed)[2]
        for seed in range(40)
    ]

    check(
        "random init sometimes lands badly",
        max(randoms) > min(randoms) * 5,
        f"sse from {min(randoms):.3f} to {max(randoms):.3f}",
    )

    check(
        "k-means++ is more reliable than random",
        sum(plusplus) / 40 <= sum(randoms) / 40,
        f"mean sse: ++ {sum(plusplus) / 40:.3f} "
        f"vs random {sum(randoms) / 40:.3f}",
    )

    print(
        "\n  Blob recovery over 40 seeds (SSE < 1): "
        f"random {sum(value < 1 for value in randoms)}/40, "
        f"++ {sum(value < 1 for value in plusplus)}/40"
    )
    print("  Empty clusters keep their previous centroid.")
    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")

    return 1 if fails else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.verify:
        raise SystemExit(verify())

    parser.print_help()