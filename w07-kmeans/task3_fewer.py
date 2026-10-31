#!/usr/bin/env python3
"""Task 3: exact k-means with Hamerly-style bounds.

실행:
    python3 bench.py --yours

bench.py는 수정하지 않는다.
모든 점-중심 및 중심-중심 거리 계산에 전달받은 distance를 사용한다.
"""


class NaiveKMeans:
    """원본 기준 구현: 매 반복 모든 점과 모든 중심을 비교한다."""

    def __init__(self, k, max_iter=50):
        self.k, self.max_iter = k, max_iter

    def run(self, points, initial_centroids, distance):
        centroids = list(initial_centroids)
        labels = [None] * len(points)

        for self.iterations in range(1, self.max_iter + 1):
            changed = False

            for i, point in enumerate(points):
                best, best_index = None, 0

                for j, centroid in enumerate(centroids):
                    value = distance(point, centroid)

                    if best is None or value < best - 1e-12:
                        best, best_index = value, j

                if labels[i] != best_index:
                    labels[i] = best_index
                    changed = True

            centroids = _means(
                points, labels, self.k, centroids
            )

            if not changed:
                break

        return labels, centroids


def _means(points, labels, k, previous):
    """원본과 같은 순서로 평균을 계산하고 빈 중심은 유지한다."""
    result = []

    for index in range(k):
        group = [
            point
            for point, label in zip(points, labels)
            if label == index
        ]

        if group:
            result.append(
                tuple(
                    sum(values) / len(group)
                    for values in zip(*group)
                )
            )
        else:
            result.append(previous[index])

    return result


class YourKMeans:
    """점마다 상한 1개와 하한 1개를 유지하는 정확한 가지치기.

    upper[i]:
        점 i와 현재 배정 중심 사이 거리의 상한.

    lower[i]:
        점 i와 현재 배정 중심을 제외한 모든 중심 사이
        최소 거리의 하한.

    separation[j]:
        중심 j와 다른 중심 사이 최소 거리의 절반.

    upper < max(lower, separation)이면 재배정할 필요가 없다.
    경계와 동률 부근에서는 실제 거리를 계산한다.
    """

    EPS = 1e-12

    def __init__(self, k, max_iter=50):
        if k < 1 or max_iter < 1:
            raise ValueError("k and max_iter must be positive.")

        self.k = k
        self.max_iter = max_iter
        self.iterations = 0

        self.distance_calls = 0
        self.first_iteration_calls = 0
        self.pruned_by_lower = 0
        self.pruned_by_separation = 0
        self.full_scans = 0

    @staticmethod
    def _safely_less(upper, bound):
        """부동소수점 오차와 기준 구현의 동률 허용 범위에 여유를 둔다."""
        if bound == float("inf"):
            return True

        margin = 1e-10 * max(
            1.0, abs(upper), abs(bound)
        )
        return upper + margin < bound

    def run(self, points, initial_centroids, distance):
        if len(initial_centroids) != self.k:
            raise ValueError(
                "initial_centroids must contain k centroids."
            )

        self.iterations = 0
        self.distance_calls = 0
        self.first_iteration_calls = 0
        self.pruned_by_lower = 0
        self.pruned_by_separation = 0
        self.full_scans = 0

        centroids = list(initial_centroids)

        if not points:
            return [], centroids

        n = len(points)
        labels = [None] * n
        upper = [float("inf")] * n
        lower = [0.0] * n

        def measured(a, b):
            self.distance_calls += 1
            return distance(a, b)

        def full_assignment(point):
            # 기준 구현과 같은 중심 순서 및 동률 처리.
            values = [
                measured(point, centroid)
                for centroid in centroids
            ]

            best_index = 0
            best = values[0]

            for index in range(1, self.k):
                if values[index] < best - self.EPS:
                    best = values[index]
                    best_index = index

            other_lower = min(
                (
                    value
                    for index, value in enumerate(values)
                    if index != best_index
                ),
                default=float("inf"),
            )

            self.full_scans += 1
            return best_index, best, other_lower

        def can_skip(i, separation):
            current = labels[i]
            lower_ok = self._safely_less(
                upper[i], lower[i]
            )
            separation_ok = self._safely_less(
                upper[i], separation[current]
            )

            if not lower_ok and not separation_ok:
                return False

            # 두 조건이 모두 참이면 더 큰 경계를 제공한 쪽에 기록.
            if lower_ok and (
                not separation_ok
                or lower[i] >= separation[current]
            ):
                self.pruned_by_lower += 1
            else:
                self.pruned_by_separation += 1

            return True

        for iteration in range(1, self.max_iter + 1):
            self.iterations = iteration
            changed = False

            if iteration == 1:
                # 첫 반복은 아직 점별 경계가 없으므로 전부 계산한다.
                for i, point in enumerate(points):
                    label, exact, second = full_assignment(point)
                    labels[i] = label
                    upper[i] = exact
                    lower[i] = second

                changed = True

            else:
                separation = [float("inf")] * self.k

                # 중심-중심 거리도 반드시 카운터에 포함한다.
                for a in range(self.k):
                    for b in range(a + 1, self.k):
                        half = measured(
                            centroids[a], centroids[b]
                        ) / 2.0

                        separation[a] = min(
                            separation[a], half
                        )
                        separation[b] = min(
                            separation[b], half
                        )

                for i, point in enumerate(points):
                    if can_skip(i, separation):
                        continue

                    current = labels[i]

                    # 느슨해진 상한을 현재의 정확한 거리로 좁힌다.
                    upper[i] = measured(
                        point, centroids[current]
                    )

                    if can_skip(i, separation):
                        continue

                    # 안전하게 제외할 수 없는 점만 전체 비교한다.
                    # 현재 중심 거리의 중복 계산도 실제 호출로 계수된다.
                    label, exact, second = full_assignment(point)

                    if label != current:
                        labels[i] = label
                        changed = True

                    upper[i] = exact
                    lower[i] = second

            new_centroids = _means(
                points, labels, self.k, centroids
            )

            if not changed:
                centroids = new_centroids
                break

            if iteration == self.max_iter:
                centroids = new_centroids

                if iteration == 1:
                    self.first_iteration_calls = self.distance_calls

                break

            movements = [
                measured(old, new)
                for old, new in zip(centroids, new_centroids)
            ]
            maximum_movement = max(movements)

            # 삼각부등식으로 다음 반복의 유효한 경계를 갱신한다.
            for i in range(n):
                upper[i] += movements[labels[i]]
                lower[i] = max(
                    0.0,
                    lower[i] - maximum_movement,
                )

            centroids = new_centroids

            if iteration == 1:
                self.first_iteration_calls = self.distance_calls

        self.first_iteration_fraction = (
            self.first_iteration_calls / self.distance_calls
            if self.distance_calls
            else 0.0
        )

        return labels, centroids