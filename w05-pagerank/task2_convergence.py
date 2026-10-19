#!/usr/bin/env python3
"""Week 5 · Task 2 — How long does it take to converge, and on what?

Textbook §5.1, §5.2.

This program measures how PageRank convergence changes according to:

    1. beta
    2. graph size
    3. tolerance

Results are accumulated in out/convergence.json.

Examples:

    python task2_convergence.py --reset \
        --betas 0.5,0.7,0.85,0.95,0.99

    python task2_convergence.py \
        --nodes 20000 \
        --betas 0.85,0.95

    python task2_convergence.py \
        --tol 1e-3 \
        --betas 0.85
"""

import argparse
import ctypes
import json
import os
import platform
import time


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
RESULT_PATH = os.path.join(OUT, "convergence.json")


def total_ram_gb():
    """Return total physical RAM in GiB when it can be detected."""

    # Windows
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)

        try:
            success = ctypes.windll.kernel32.GlobalMemoryStatusEx(
                ctypes.byref(status)
            )

            if success:
                return round(
                    status.ullTotalPhys / (1024 ** 3),
                    1
                )

        except (AttributeError, OSError):
            return None

    # Linux and other Unix-like systems
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        physical_pages = os.sysconf("SC_PHYS_PAGES")

        return round(
            page_size * physical_pages / (1024 ** 3),
            1
        )

    except (AttributeError, ValueError, OSError):
        return None


def machine(running_programs):
    """Record the machine used for the timing experiment."""

    cpu_name = (
        platform.processor()
        or os.environ.get("PROCESSOR_IDENTIFIER")
        or platform.machine()
    )

    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "processor": cpu_name,
        "ram_gb": total_ram_gb(),
        "python": platform.python_version(),
        "running_programs": running_programs,
    }


def parse_betas(value):
    """Parse and validate the comma-separated beta list."""

    try:
        betas = [
            float(item.strip())
            for item in value.split(",")
            if item.strip()
        ]

    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "betas must be comma-separated numbers"
        ) from error

    if not betas:
        raise argparse.ArgumentTypeError(
            "at least one beta is required"
        )

    for beta in betas:
        if not 0.0 <= beta <= 1.0:
            raise argparse.ArgumentTypeError(
                "every beta must be between 0 and 1"
            )

    return betas


def load_previous_results(reset):
    """Load prior measurements unless --reset was selected."""

    if reset or not os.path.exists(RESULT_PATH):
        return {
            "machine": {},
            "runs": [],
        }

    try:
        with open(
            RESULT_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

    except (json.JSONDecodeError, OSError):
        return {
            "machine": {},
            "runs": [],
        }

    if not isinstance(data, dict):
        return {
            "machine": {},
            "runs": [],
        }

    if not isinstance(data.get("runs"), list):
        data["runs"] = []

    return data


def save_results(data):
    """Save all accumulated measurements."""

    os.makedirs(OUT, exist_ok=True)

    with open(
        RESULT_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--betas",
        default="0.5,0.7,0.85,0.95,0.99",
        help="comma-separated beta values"
    )

    parser.add_argument(
        "--nodes",
        type=int,
        default=None,
        help="graph size; default is the harness graph"
    )

    parser.add_argument(
        "--tol",
        type=float,
        default=1e-10,
        help="L1 convergence tolerance"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="discard earlier convergence measurements"
    )

    parser.add_argument(
        "--running",
        default=(
            "Visual Studio Code, KakaoTalk, "
            "File Explorer, Chrome, ChatGPT"
        ),
        help="programs running during the experiment"
    )

    args = parser.parse_args()

    if args.nodes is not None and args.nodes <= 0:
        parser.error("--nodes must be positive")

    if args.tol <= 0:
        parser.error("--tol must be positive")

    try:
        betas = parse_betas(args.betas)

    except argparse.ArgumentTypeError as error:
        parser.error(str(error))

    os.makedirs(OUT, exist_ok=True)

    import bench

    if args.nodes is not None:
        bench.NODES = args.nodes

    graph = bench.build()

    from task1_pagerank import pagerank

    rows = []

    print()
    print(
        f"  graph nodes {len(graph):,}, "
        f"tolerance {args.tol:g}"
    )
    print()

    for beta in betas:
        start = time.perf_counter()

        ranks = pagerank(
            graph,
            beta=beta,
            iterations=500,
            tol=args.tol
        )

        elapsed = time.perf_counter() - start

        iterations_used = getattr(
            pagerank,
            "iterations",
            None
        )

        top = sorted(
            ranks.items(),
            key=lambda item: (-item[1], item[0])
        )[:10]

        row = {
            "beta": beta,
            "nodes": len(graph),
            "tol": args.tol,
            "iterations": iterations_used,
            "seconds": elapsed,
            "top10": [
                node
                for node, _ in top
            ],
        }

        rows.append(row)

        top_three = ", ".join(
            node
            for node, _ in top[:3]
        )

        print(
            f"  beta {beta:<5}  "
            f"{str(iterations_used):>4} iterations  "
            f"{elapsed:>7.3f}s   "
            f"top: {top_three}"
        )

    data = load_previous_results(args.reset)

    data["machine"] = machine(args.running)
    data["runs"].extend(rows)

    save_results(data)

    print()
    print(
        f"  -> out/convergence.json  "
        f"({len(data['runs'])} run(s))"
    )


if __name__ == "__main__":
    main()