"""Verify bundled file hashes and candidate-manifest relationships, using stdlib only."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

def records(name):
    return [json.loads(line) for line in (ROOT / "data/manifests" / name).read_text().splitlines()]

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
    print(f"Verified {checked} file checksums and candidate-manifest relationships.")
    print("This is package validation, not reproduction of the published experiments.")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        sys.exit(f"Validation failed: {error}")
