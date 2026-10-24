"""Command-line entry point.

    uv run python src/cli.py generate [--seed 2024] [--out data]
"""

import argparse
from pathlib import Path

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Fraud detection scoring engine (Papaya AI Challenge 10)")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="generate claims.csv and ground_truth.csv")
    generate.add_argument("--seed", type=int, default=DEFAULT_SEED)
    generate.add_argument("--out", type=Path, default=DATA_DIR, help="output directory (default: data/)")
    generate.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
