#!/usr/bin/env python3
"""Task 2: distance concentration in high dimensions.

기본 실행은 7개 차원과 고정 차원에서의 점 개수 비교를 수행한다.
실제로 실행한 결과만 out/curse.json 및 out/curse.md에 저장한다.

실행:
    python3 task2_curse.py
    python3 task2_curse.py --dims 500,1000 --points 2000

점 개수 비교:
    python3 task2_curse.py --dims 100 --points 1000 \
        --compare-points 250,2000,5000 --compare-dim 100
"""

import argparse
import datetime
import json
import math
import os
import platform
import random
import statistics
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def machine():
    info = {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "logical_cpus": os.cpu_count(),
    }

    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as key:
                info["processor"] = winreg.QueryValueEx(
                    key, "ProcessorNameString"
                )[0].strip()
        except OSError:
            pass

    return info


def euclid(a, b):
    return math.sqrt(
        sum((x - y) ** 2 for x, y in zip(a, b))
    )


def sample_distances(n, dim, pairs, seed=246):
    """서로 다른 두 점을 선택해 정확히 pairs개의 거리를 측정한다.

    쌍은 복원추출하므로 동일한 쌍이 여러 번 선택될 수 있다.
    """
    if n < 2 or dim < 1 or pairs < 1:
        raise ValueError("n >= 2, dim >= 1, pairs >= 1 required.")

    rng = random.Random(seed + dim)

    points = [
        tuple(rng.random() for _ in range(dim))
        for _ in range(n)
    ]

    distances = []

    for _ in range(pairs):
        i = rng.randrange(n)
        j = rng.randrange(n - 1)

        if j >= i:
            j += 1

        distances.append(euclid(points[i], points[j]))

    return distances


def measure(n, dim, pairs, seed, environment, session):
    start = time.perf_counter()
    distances = sample_distances(n, dim, pairs, seed)
    elapsed = time.perf_counter() - start

    low = min(distances)
    high = max(distances)
    mean = statistics.fmean(distances)
    stdev = statistics.pstdev(distances)

    return {
        "dim": dim,
        "points": n,
        "pairs": len(distances),
        "seed": seed,
        "min": low,
        "max": high,
        "mean": mean,
        "stdev": stdev,
        "contrast": (high - low) / low if low else None,
        "relative_stdev": stdev / mean if mean else None,
        "mean_over_sqrt_dim": mean / math.sqrt(dim),
        "seconds": elapsed,
        "session": session,
        "machine": environment,
    }


def number(value, digits=4):
    return "undefined" if value is None else f"{value:.{digits}f}"


def write_report(data, current_rows):
    lines = [
        "# Task 2 — Curse of dimensionality",
        "",
        "## Measurement method",
        "",
        "Uniform points in [0, 1]^d. Each sampled pair contains two "
        "different point indices; pairs are sampled with replacement.",
        "Minimum and maximum are sampled extremes, not the exact "
        "nearest/farthest distances among all possible pairs.",
        "Each row is one timed run. Time includes point generation "
        "and distance sampling, but excludes file writing.",
        "",
        "## Environment",
        "",
        "```json",
        json.dumps(data["machine"], indent=2, ensure_ascii=False),
        "```",
        "",
        "Other running applications were not automatically inspected.",
        "Historical rows retain their own machine and session metadata "
        "in curse.json.",
        "",
        "## Measured table",
        "",
        "| Session | n | d | Pairs | Min | Max | Mean | SD | "
        "Contrast | SD / mean | Mean / sqrt(d) | Seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in data["runs"]:
        normalized = row["mean"] / math.sqrt(row["dim"])

        lines.append(
            f"| {row.get('session', 'legacy')} "
            f"| {row['points']} | {row['dim']} | {row['pairs']} "
            f"| {row['min']:.4f} | {row['max']:.4f} "
            f"| {row['mean']:.4f} | {row['stdev']:.4f} "
            f"| {number(row['contrast'])} "
            f"| {number(row['relative_stdev'])} "
            f"| {normalized:.4f} | {row['seconds']:.3f} |"
        )

    # 同じ環境・seed・サンプル数の記録のみを比較する。
    # 同一 n,d の再実行がある場合は最新記録を使う。
    comparable = {}

    for row in data["runs"]:
        if row.get("machine") != data["machine"]:
            continue

        key = (
            row.get("seed", 246),
            row["pairs"],
            row["points"],
            row["dim"],
        )
        comparable[key] = row

    groups = {}

    for (seed, pairs, n, dim), row in comparable.items():
        groups.setdefault((seed, pairs, n), []).append(row)

    lines += ["", "## A3: contrast thresholds", ""]

    for (seed, pairs, n), rows in sorted(groups.items()):
        rows.sort(key=lambda row: row["dim"])

        lines.append(
            f"- n={n}, seed={seed}, sampled pairs={pairs}:"
        )

        for threshold in (1.0, 0.5):
            below = [
                row["dim"]
                for row in rows
                if row["contrast"] is not None
                and row["contrast"] < threshold
            ]

            if below:
                lines.append(
                    f"  - First tested dimension with contrast "
                    f"< {threshold}: d={min(below)}."
                )
            else:
                lines.append(
                    f"  - Contrast < {threshold} was not observed "
                    f"in the tested dimensions."
                )

    lines += [
        "",
        "These are first observed crossings on the tested grid, "
        "not exact thresholds. Sampled extremes may fluctuate.",
        "",
        "## A4: growth of mean distance",
        "",
        "For independent uniform coordinates, E[(X-Y)^2] = 1/6, "
        "so E[distance^2] = d/6. At high dimension, concentration "
        "suggests mean distance approximately sqrt(d/6), rather "
        "than linear growth in d.",
        "The table reports mean / sqrt(d); compare it with "
        f"1/sqrt(6) = {1 / math.sqrt(6):.4f}. "
        "This is an asymptotic comparison, not an exact formula "
        "for mean distance at small d.",
        "",
        "## A5: relative standard deviation",
        "",
        "SD / mean measures concentration across the sampled distance "
        "distribution, while contrast depends on just its sampled "
        "minimum and maximum. Relative SD is usually more stable "
        "for describing typical concentration; contrast is useful "
        "for examining the observed range.",
        "A small relative SD does not prove that every nearest-neighbor "
        "task is useless: structured data can differ from uniform "
        "points in a cube.",
        "",
        "## A6: varying point count at a fixed dimension",
        "",
    ]

    by_dimension = {}

    for (seed, pairs, n, dim), row in comparable.items():
        by_dimension.setdefault((seed, pairs, dim), []).append(row)

    comparisons = 0

    for (seed, pairs, dim), rows in sorted(by_dimension.items()):
        rows.sort(key=lambda row: row["points"])

        if len(rows) < 2:
            continue

        comparisons += 1
        values = "; ".join(
            f"n={row['points']}: contrast="
            f"{number(row['contrast'])}, relative SD="
            f"{number(row['relative_stdev'])}"
            for row in rows
        )

        lines.append(
            f"- d={dim}, seed={seed}, sampled pairs={pairs}: {values}."
        )

    if not comparisons:
        lines.append(
            "No comparable point-count experiment is recorded yet."
        )

    lines += [
        "",
        "Changing n changes the finite point cloud and the chance of "
        "resampling the same pair. However, this experiment keeps "
        "the sampled pair count fixed instead of examining all "
        "n(n-1)/2 pairs. A monotonic increase in sampled contrast "
        "with n is therefore not guaranteed, and a single run does "
        "not isolate a systematic n effect from sampling variation.",
        "",
        "## A7: runtime",
        "",
    ]

    largest = max(
        current_rows,
        key=lambda row: (
            row["dim"],
            row["points"],
            row["pairs"],
        ),
    )
    slowest = max(current_rows, key=lambda row: row["seconds"])

    lines += [
        f"- Largest dimension in the current invocation: "
        f"d={largest['dim']}, n={largest['points']}, "
        f"pairs={largest['pairs']}; "
        f"{largest['seconds']:.3f} seconds.",
        f"- Slowest run in the current invocation: "
        f"d={slowest['dim']}, n={slowest['points']}; "
        f"{slowest['seconds']:.3f} seconds.",
        "",
        "## A8: connection to Week 3 Jaccard LSH",
        "",
        "This experiment measures Euclidean distances between uniform "
        "dense vectors. Week 3 uses Jaccard similarity between shingle "
        "sets, so this result does not directly establish that "
        "Jaccard LSH fails.",
        "MinHash collision probability tracks Jaccard similarity. "
        "LSH is useful when relevant and irrelevant pairs have "
        "different similarities; if those similarities themselves "
        "concentrate, distinguishing pairs becomes difficult. "
        "The relevant similarity distribution must be measured "
        "instead of transferring a Euclidean result unchanged.",
        "",
    ]

    (OUT / "curse.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_int_list(text):
    return [
        int(value.strip())
        for value in text.split(",")
        if value.strip()
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dims", default="2,5,10,20,50,100,200")
    parser.add_argument("--points", type=int, default=1000)
    parser.add_argument("--pairs", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=246)
    parser.add_argument("--compare-points", default="250,2000")
    parser.add_argument("--compare-dim", type=int, default=100)
    args = parser.parse_args()

    try:
        dimensions = parse_int_list(args.dims)
        comparison_counts = parse_int_list(args.compare_points)
    except ValueError:
        parser.error("Dimensions and point counts must be integers.")

    if not dimensions or any(dim < 1 for dim in dimensions):
        parser.error("--dims must contain positive dimensions.")

    if args.points < 2 or any(n < 2 for n in comparison_counts):
        parser.error("Point counts must be at least 2.")

    if args.pairs < 1 or args.compare_dim < 1:
        parser.error("--pairs and --compare-dim must be positive.")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "curse.json"

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    else:
        data = {"runs": []}

    environment = machine()
    data["machine"] = environment

    session = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat(timespec="microseconds")

    jobs = [
        (args.points, dimension)
        for dimension in dimensions
    ]

    if comparison_counts:
        jobs.extend(
            (n, args.compare_dim)
            for n in [args.points, *comparison_counts]
        )

    # 동일한 점 개수와 차원의 중복 실행 방지.
    jobs = list(dict.fromkeys(jobs))
    current_rows = []

    for n, dimension in jobs:
        row = measure(
            n,
            dimension,
            args.pairs,
            args.seed,
            environment,
            session,
        )

        current_rows.append(row)
        data["runs"].append(row)

        # 긴 실행 중 중단되어도 완료한 측정은 남긴다.
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(
            f"  n {n:>6}   dim {dimension:>5}   "
            f"mean {row['mean']:>8.4f}   "
            f"contrast {number(row['contrast']):>10}   "
            f"rel.sd {number(row['relative_stdev']):>8}   "
            f"{row['seconds']:.3f}s",
            flush=True,
        )

    write_report(data, current_rows)

    print(f"\n  -> {OUT / 'curse.json'}")
    print(f"  -> {OUT / 'curse.md'}")


if __name__ == "__main__":
    main()