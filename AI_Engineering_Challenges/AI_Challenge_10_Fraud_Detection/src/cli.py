"""Command-line entry point.

    uv run python src/cli.py generate [--seed 2024] [--out data]
    uv run python src/cli.py check [--data data]
    uv run python src/cli.py score [--data data] [--weights src/config/weights.json] [--out output]
    uv run python src/cli.py metrics [--data data] [--weights src/config/weights.json] [--out output]
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

from catalog import CatalogError, load_catalog
from claims import ClaimsError, load_claims
from generator.checks import check_dataset
from generator.dataset import DEFAULT_SEED, build_dataset, summary, write_dataset
from metrics.evaluate import GroundTruthError, evaluate, load_ground_truth, load_phantom_day_claims
from metrics.report import build_report, write_report
from rule_names import ALL_RULES
from scoring.score import score_claims, write_scored
from scoring.weights import DEFAULT_PATH as DEFAULT_WEIGHTS, WeightsError, load_weights

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


def run_score(args: argparse.Namespace) -> tuple[list[dict], float, dict]:
    """Load -> rules -> score -> write scored_output.json. Returns (results, elapsed seconds, weights); exits 1 on error."""
    start = time.perf_counter()
    try:
        catalog = load_catalog()
        weights = load_weights(args.weights)
        claims = load_claims(args.data / "claims.csv", catalog)
    except (CatalogError, WeightsError, ClaimsError) as exc:
        print("Cannot score:", file=sys.stderr)
        print(f"  {exc}", file=sys.stderr)
        sys.exit(1)
    results = score_claims(claims, catalog, weights)
    try:
        path = write_scored(results, args.out)
    except OSError as exc:
        print(f"Cannot write {args.out}: {exc}", file=sys.stderr)
        sys.exit(1)
    elapsed = time.perf_counter() - start
    print(f"Scored {len(results)} claims in {elapsed:.3f} s; wrote {path}")
    return results, elapsed, weights


def cmd_score(args: argparse.Namespace) -> None:
    results, _, _ = run_score(args)
    flagged = [r for r in results if r["flags"]]
    per_rule = Counter(f["rule"] for r in results for f in r["flags"])
    print(f"Claims with at least one flag: {len(flagged)} of {len(results)}")
    print("Claims per rule:")
    for rule in ALL_RULES:
        print(f"  {rule:<30} {per_rule[rule]:>4}")
    print("Top 10 by risk score:")
    for r in results[:10]:
        print(f"  {r['claim_id']}  {r['risk_score']:>3}  {', '.join(f['rule'] for f in r['flags'])}")


def cmd_metrics(args: argparse.Namespace) -> None:
    results, elapsed, weights = run_score(args)
    try:
        truth = load_ground_truth(args.data / "ground_truth.csv")
        evaluation = evaluate(results, truth, load_phantom_day_claims(args.data))
        path = write_report(build_report(evaluation, weights, elapsed, args.data), args.out)
    except (GroundTruthError, OSError) as exc:
        print("Cannot evaluate:", file=sys.stderr)
        for line in str(exc).splitlines():
            print(f"  {line}", file=sys.stderr)
        sys.exit(1)
    overall = evaluation["overall"]
    print(f"Precision {overall['precision']:.1%}, recall {overall['recall']:.1%}, FPR {overall['fpr']:.1%}")
    print(f"Wrote {path}")


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

    score = commands.add_parser("score", help="score claims.csv and write the ranked scored_output.json")
    score.add_argument("--data", type=Path, default=DATA_DIR, help="directory holding claims.csv (default: data/)")
    score.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS, help="severity weights JSON (default: src/config/weights.json)")
    score.add_argument("--out", type=Path, default=PROJECT_ROOT / "output", help="output directory (default: output/)")
    score.set_defaults(func=cmd_score)

    metrics = commands.add_parser("metrics", help="score claims, then compare with ground_truth.csv and write metrics_report.md")
    metrics.add_argument("--data", type=Path, default=DATA_DIR, help="directory holding claims.csv and ground_truth.csv (default: data/)")
    metrics.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS, help="severity weights JSON (default: src/config/weights.json)")
    metrics.add_argument("--out", type=Path, default=PROJECT_ROOT / "output", help="output directory (default: output/)")
    metrics.set_defaults(func=cmd_metrics)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
