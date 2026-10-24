"""Command-line entry point.

    uv run python src/cli.py generate [--seed 2024] [--out data]
    uv run python src/cli.py check [--data data]
"""

import argparse
import sys
from pathlib import Path

from catalog import load_catalog
from generator.checks import check_dataset
from generator.dataset import DEFAULT_SEED, build_dataset, summary, write_dataset

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def cmd_generate(args: argparse.Namespace) -> None:
    dataset = build_dataset(args.seed)
    write_dataset(dataset, args.out)
    info = summary(dataset)
    print(f"Wrote {info['total_claims']} claims ({info['fraud_claims']} fraud) to {args.out} with seed {args.seed}")
    for pattern, count in info["claims_per_pattern"].items():
        print(f"  {pattern:<30} {count:>4}")
    print("Run `check` to verify the files.")


def cmd_check(args: argparse.Namespace) -> None:
    problems, stats = check_dataset(args.data, load_catalog())
    if problems:
        print(f"Structural checks FAILED for {args.data}; do not use these files:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    print(f"Structural checks passed for {args.data}: {stats['claims']} claims, {stats['fraud']} fraud")
    for pattern, count in stats["claims_per_pattern"].items():
        print(f"  {pattern:<30} {count:>4}")
    low, high = stats["weekday_only_claims"]
    print(f"  members {stats['members']}, providers {stats['providers']}, claims per provider type {stats['claims_per_provider_type']}")
    print(f"  weekday-only hospitals {low}-{high} claims, min single-code claims per code {stats['min_single_code_claims']}")
    print(f"  duplicate groups {stats['duplicate_groups']}, phantom day {stats['phantom_day']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fraud detection scoring engine (Papaya AI Challenge 10)")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="generate claims.csv and ground_truth.csv")
    generate.add_argument("--seed", type=int, default=DEFAULT_SEED)
    generate.add_argument("--out", type=Path, default=DATA_DIR, help="output directory (default: data/)")
    generate.set_defaults(func=cmd_generate)

    check = commands.add_parser("check", help="run structural checks on an existing dataset")
    check.add_argument("--data", type=Path, default=DATA_DIR, help="dataset directory (default: data/)")
    check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
