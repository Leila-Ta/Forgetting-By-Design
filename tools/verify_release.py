"""Verify bundled file hashes and candidate-manifest relationships, using stdlib only."""
from pathlib import Path
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

def records(name, directory="manifests"):
    return [json.loads(line) for line in (ROOT / "data" / directory / name).read_text().splitlines()]

def main():
    checked = 0
    seen = set()
    for line in (ROOT / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or name in seen:
            raise ValueError("Invalid or duplicate checksum path")
        seen.add(name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")
        checked += 1
    pool = records("forget_pool.jsonl")
    resolved = records("forget_resolved.jsonl")
    keep = records("keep_person_pairs.jsonl")
    poolmask = set((ROOT / "data/scopes/pool_630.txt").read_text().splitlines())
    resolvedmask = set((ROOT / "data/scopes/resolved_605.txt").read_text().splitlines())
    if len(pool) != 3690 or len({r["qid"] for r in pool}) != 3690 or {r["target_docid"] for r in pool} != poolmask or len(poolmask) != 630:
        raise ValueError("Unexpected candidate pool manifest")
    if len(resolved) != 3542 or len({r["qid"] for r in resolved}) != 3542 or {r["target_docid"] for r in resolved} != resolvedmask or len(resolvedmask) != 605:
        raise ValueError("Unexpected resolved candidate manifest")
    for filename, base, count in [("forget_1000.qids", pool, 1000), ("robustness_200.qids", resolved, 200)]:
        ids = (ROOT / "data/manifests" / filename).read_text().splitlines()
        if len(ids) != count or len(set(ids)) != count or not set(ids) <= {r["qid"] for r in base}:
            raise ValueError(f"Invalid frozen selection: {filename}")
    if len(keep) != 10140 or len({r["qid"] for r in keep}) != 9855 or len({(r["qid"], r["target_docid"]) for r in keep}) != 10140:
        raise ValueError("Unexpected Keep query-target pairs")
    if {r["target_docid"] for r in keep} & (poolmask | resolvedmask):
        raise ValueError("Candidate lawful targets overlap a supplied exact-ID scope")
    generation = records("generation_200perkind.jsonl", "annotations")
    diagnostic = records("diagnostic_20perstate.jsonl", "annotations")
    if len(generation) != 1200 or len({(r["kind"], r["qid"], r["condition"]) for r in generation}) != 1200:
        raise ValueError("Unexpected 200-per-kind annotation population")
    if any(sum(r["kind"] == kind and r["condition"] == state for r in generation) != 200
           for kind in ["forget", "keep"] for state in ["PRE", "POST", "FILT"]):
        raise ValueError("Unbalanced candidate annotation group")
    if len(diagnostic) != 60 or len({(r["qid"], r["condition"]) for r in diagnostic}) != 60:
        raise ValueError("Unexpected separate diagnostic population")
    if sum(r["csr"] is None for r in diagnostic) != 31 or any(
        r["csr"] is None and not (r["abstain"] == 1 and r["nonfinite_normalization"] == {"csr": "NaN"})
        for r in diagnostic):
        raise ValueError("CSR undefined-value provenance mismatch")
    gold = set((ROOT / "data/scopes/forget_gold_targets_778.txt").read_text().splitlines())
    with (ROOT / "data/ranks/forget_multi_target_PRE_POST.tsv").open(newline="") as handle:
        rank_rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(gold) != 778 or {r["target_docid"] for r in rank_rows} != gold or not (poolmask | resolvedmask) <= gold:
        raise ValueError("Unexpected diagnostic gold-target universe")
    print(f"Verified {checked} file checksums and candidate-manifest relationships.")
    print("This is package validation, not reproduction of the published experiments.")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        sys.exit(f"Validation failed: {error}")
