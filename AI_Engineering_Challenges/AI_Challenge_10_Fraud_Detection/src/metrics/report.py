"""Build output/metrics_report.md from evaluate() results. Spec: docs/business-rule/metrics.md (4 parts)."""

import json
from pathlib import Path

from rule_names import ALL_RULES

REPORT_NAME = "metrics_report.md"
TARGET_RECALL = 0.70
TARGET_FPR = 0.20


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def read_seed(data_dir: Path | None) -> int | None:
    """Seed from generation_summary.json, or None when the file or key is missing/unreadable."""
    if data_dir is None:
        return None
    try:
        return json.loads((Path(data_dir) / "generation_summary.json").read_text(encoding="utf-8")).get("seed")
    except (OSError, ValueError, AttributeError):
        return None


def build_report(evaluation: dict, weights: dict[str, int], elapsed: float, data_dir: Path | None = None) -> str:
    overall = evaluation["overall"]
    total_claims = overall["tp"] + overall["fp"] + overall["fn"] + overall["tn"]
    fraud_claims = overall["tp"] + overall["fn"]
    seed = read_seed(data_dir)

    out = ["# Metrics report", ""]
    seed_text = f"seed {seed}" if seed is not None else "seed unknown (generation_summary.json missing or unreadable)"
    out.append(f"- Dataset: {total_claims:,} claims, {fraud_claims:,} fraudulent, {seed_text}")
    out.append("- Severity weights: " + ", ".join(f"{rule} {weights[rule]}" for rule in ALL_RULES))
    out.append(
        f"- Runtime: Scored {total_claims:,} claims in {elapsed:.3f} s "
        "(load -> rules -> score -> write, measured in-process with time.perf_counter; Python startup excluded)"
    )
    out.append("- Prediction rule: a claim is predicted fraud when risk_score > 0 (at least one flag)")

    recall_ok = overall["recall"] >= TARGET_RECALL
    fpr_ok = overall["fpr"] <= TARGET_FPR
    out += ["", "## 1. Overall", ""]
    out.append(table(
        ["TP", "FP", "FN", "TN", "Precision", "Recall", "FPR"],
        [[f"{overall[k]:,}" for k in ("tp", "fp", "fn", "tn")]
         + [pct(overall["precision"]), pct(overall["recall"]), pct(overall["fpr"])]],
    ))
    out += ["", (
        f"Recall {pct(overall['recall'])} vs target >= {TARGET_RECALL:.0%}: {'met' if recall_ok else 'NOT met'}. "
        f"FPR {pct(overall['fpr'])} vs target <= {TARGET_FPR:.0%}: {'met' if fpr_ok else 'NOT met'}. "
        "The dataset is synthetic and generated from the same rule definitions the engine applies, "
        "so these numbers are an upper bound for real data; see Limitations in README.md."
    )]

    out += ["", "## 2. By pattern", ""]
    patterns = evaluation["by_pattern"]
    out.append(table(
        ["Pattern", "Fraud claims", "Caught (score > 0)", "Caught by own rule", "Recall"],
        [[p["pattern"], f"{p['fraud']:,}", f"{p['caught']:,}", f"{p['caught_by_own_rule']:,}",
          pct(p["caught"] / p["fraud"]) if p["fraud"] else "n/a"]
         for p in patterns],
    ))
    empty = [p["pattern"] for p in patterns if not p["fraud"]]
    weak = [p["pattern"] for p in patterns if p["fraud"] and p["caught"] < p["fraud"]]
    not_own = [p["pattern"] for p in patterns if p["caught_by_own_rule"] < p["caught"]]
    sentences = ["Patterns with misses: " + ", ".join(weak) + "." if weak else "Every pattern that has fraud claims is fully caught."]
    if empty:
        sentences.append("No fraud claims for: " + ", ".join(empty) + " (recall n/a).")
    if not_own:
        sentences.append("Some claims were caught only by another rule in: " + ", ".join(not_own) + ".")
    out += ["", " ".join(sentences)]

    fp = evaluation["natural_fp"]
    out += ["", "## 3. Natural false positives by rule", ""]
    out.append(table(
        ["Rule", "Flags", "On fraud claims", "On legit claims (FP)"],
        [[r["rule"], f"{r['flags']:,}", f"{r['on_fraud']:,}", f"{r['on_legit']:,}"] for r in fp["rows"]],
    ))
    noisy = sorted((r for r in fp["rows"] if r["on_legit"]), key=lambda r: -r["on_legit"])
    if noisy:
        top = ", ".join(f"{r['rule']} {r['on_legit']:,}" for r in noisy)
        sentence = (f"{fp['fp_claims']:,} distinct legit claims were flagged (a claim flagged by 2 rules counts once here "
                    f"and under each rule in the table); legit flags per rule: {top}.")
    else:
        sentence = "No legit claim was flagged."
    out += ["", sentence]

    out += ["", "## 4. Threshold table", ""]
    thresholds = evaluation["thresholds"]
    out.append(table(
        ["Predict fraud when score", "TP", "FP", "FN", "TN", "Recall", "FPR"],
        [[t["threshold"], f"{t['tp']:,}", f"{t['fp']:,}", f"{t['fn']:,}", f"{t['tn']:,}", pct(t["recall"]), pct(t["fpr"])]
         for t in thresholds],
    ))
    first, last = thresholds[0], thresholds[-1]
    sentence = (f"Raising the threshold from {first['threshold']} to {last['threshold']} takes recall from "
                f"{pct(first['recall'])} to {pct(last['recall'])} and FPR from {pct(first['fpr'])} to {pct(last['fpr'])}")
    if last["recall"] < first["recall"]:
        sentence += ": reviewers who only read high-score claims miss the fraud caught by weaker rules"
    out += ["", sentence + "."]

    extras = evaluation["extra_rules"]
    out += ["", "## Fraud claims flagged by an extra rule", ""]
    out += extra_section("Expected (phantom-day exception, see docs/business-rule/fraud-injection.md)", extras["expected"])
    out += [""]
    out += extra_section("Unexpected", extras["unexpected"])
    if not extras["checked"]:
        out += ["", "The phantom-day exception could not be checked (generation_summary.json or claims.csv unreadable), "
                    "so every extra-rule claim is listed as unexpected."]
    return "\n".join(out) + "\n"


def extra_section(title: str, rows: list[tuple[str, str, list[str]]]) -> list[str]:
    """Sub-heading, table (or 'none') and a count sentence for one group of extra-rule claims."""
    lines = [f"### {title}", ""]
    if not rows:
        return lines + ["None."]
    lines.append(table(["Claim", "Pattern", "Extra rules"], [[c, p, ", ".join(e)] for c, p, e in rows]))
    if len(rows) == 1:
        return lines + ["", "1 fraud claim carries a rule outside its own pattern."]
    return lines + ["", f"{len(rows):,} fraud claims carry a rule outside their own pattern."]


def write_report(text: str, out_dir: Path) -> Path:
    """Write the report to out_dir/metrics_report.md."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / REPORT_NAME
    path.write_text(text, encoding="utf-8")
    return path
