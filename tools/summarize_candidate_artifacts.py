"""Re-aggregate supplied annotations and explicit target-rank events.

This is new release-analysis code, not the missing original detector/scorer.
No model, NLI or retrieval is executed and no abstention rule is inferred for
the 200-case trace. Gold-target hits are not any-forbidden-record exposure.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

def read_jsonl(path):
    def bad(value):
        raise ValueError(f"Nonstandard JSON number {value}")
    return [json.loads(line, parse_constant=bad) for line in path.read_text(encoding="utf-8").splitlines()]

def generation_summary(rows, gold_targets):
    seen = set()
    groups = defaultdict(list)
    for row in rows:
        key = (row["kind"], row["qid"], row["condition"])
        if key in seen:
            raise ValueError("Duplicate kind/qid/condition annotation")
        seen.add(key)
        groups[(row["kind"], row["condition"])].append(row)
    result = []
    for (kind, state), group in sorted(groups.items()):
        n = len(group)
        item = {"kind": kind, "condition": state, "N_total": n,
                "stored_nonempty_citation_lists": sum(bool(r["cited_docids"]) for r in group),
                "stored_cited_forbidden_true": sum(r["cited_forbidden"] for r in group),
                "citation_flag_disagreements_under_gold778": sum(bool(set(r["cited_docids"]) & gold_targets) != r["cited_forbidden"] for r in group),
                "exact_INSUFFICIENT_EVIDENCE_count": sum(r["answer_is_exact_INSUFFICIENT_EVIDENCE"] for r in group),
                "abstention_metric_status": "not computed: original labels/rule absent in this trace"}
        if kind == "forget":
            for flag in ["leak_strict", "leak_fuzzy90", "leak_any"]:
                if any(type(r.get(flag)) is not bool for r in group):
                    raise ValueError(f"Missing/non-boolean stored annotation {flag}")
                item["stored_" + flag + "_count"] = sum(r[flag] for r in group)
                item["stored_" + flag + "_pct"] = 100 * item["stored_" + flag + "_count"] / n
        result.append(item)
    return result

def target_hit_summary(pool, ranks, k=10):
    targets = defaultdict(list)
    for row in ranks:
        targets[(row["index_flag"], row["qid"])].append(int(row["rank"]))
    result = []
    for state in sorted({r["index_flag"] for r in ranks}):
        present = {qid for condition, qid in targets if condition == state}
        if present != {r["qid"] for r in pool}:
            raise ValueError("Rank cohort does not equal the candidate pool; do not impute missing queries")
        for category in sorted({r["harm_category"] for r in pool}):
            subset = [r for r in pool if r["harm_category"] == category]
            hit = [any(0 < rank <= k for rank in targets[(state, row["qid"])]) for row in subset]
            denominator = sum(row["w"] for row in subset)
            result.append({"condition": state, "harm_category": category, "N_queries": len(subset),
                           "any_gold_target_hit_count": sum(hit), "any_gold_target_hit_rate": sum(hit) / len(subset),
                           "weighted_target_hit_rate": sum(row["w"] * value for row, value in zip(subset, hit)) / denominator})
    return result

def summarize(root=ROOT):
    ann = root / "data/annotations"
    generation = read_jsonl(ann / "generation_200perkind.jsonl")
    diagnostic = read_jsonl(ann / "diagnostic_20perstate.jsonl")
    gold = set((root / "data/scopes/forget_gold_targets_778.txt").read_text().splitlines())
    pool = read_jsonl(root / "data/manifests/forget_pool.jsonl")
    ranks_path = root / "data/ranks/forget_multi_target_PRE_POST.tsv"
    with ranks_path.open(newline="") as handle:
        ranks = list(csv.DictReader(handle, delimiter="\t"))
    diagnostic_groups = []
    for state in ["PRE", "POST", "FILT"]:
        rr = [r for r in diagnostic if r["condition"] == state]
        diagnostic_groups.append({"condition": state, "N_total": len(rr),
                                  "stored_abstain_count": sum(r["abstain"] for r in rr),
                                  "stored_leak_ans_count": sum(r["leak_ans"] for r in rr),
                                  "finite_CSR_count": sum(r["csr"] is not None for r in rr),
                                  "undefined_CSR_count": sum(r["csr"] is None for r in rr),
                                  "NLI_debug_rows": sum(r["leak_dbg"].get("reason") == "nli" for r in rr)})
    source_paths = [ann / "generation_200perkind.jsonl", ann / "diagnostic_20perstate.jsonl", ranks_path]
    return {"verification": "re-aggregation of supplied annotations and candidate rank events; no original scoring or model rerun",
            "generation_200perkind": generation_summary(generation, gold),
            "separate_diagnostic_20perstate": diagnostic_groups,
            "candidate_gold_target_hits_at_10": target_hit_summary(pool, ranks),
            "target_hit_caveat": "any relevant target per query, not global forbidden-handle exposure or a verified published HWE result",
            "source_sha256": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.out and args.out.exists():
        parser.exit(2, "Output exists; choose a new name.\n")
    try:
        text = json.dumps(summarize(), indent=2, allow_nan=False) + "\n"
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"Cannot summarize candidate annotations: {error}\n")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")

if __name__ == "__main__":
    main()
