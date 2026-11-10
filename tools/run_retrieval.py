"""Validate a fresh single-condition run, then invoke the unmodified supplied runner.

This wrapper adds input/output guards. It does not change search, ranking or
filtering and does not implement index construction, generation or scoring.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "scripts/original/run_stageB.py"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def preflight(condition, jobs, index, out, forbidden, k, M):
    if k < 1 or M < k:
        raise ValueError("Require M >= k >= 1")
    if out.exists() or out.with_suffix(out.suffix + ".run.json").exists():
        raise ValueError("Output already exists. Choose a new output name; this wrapper never appends/resumes.")
    if not index.is_dir():
        raise ValueError("Index must be a complete local index directory")
    if not forbidden.is_file() or not forbidden.read_text(encoding="utf-8").strip():
        raise ValueError("A nonempty forbidden-ID file is required in every condition")
    with jobs.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not {"qid", "query"}.issubset(reader.fieldnames or []):
            raise ValueError("Jobs require qid and query columns")
        rows = list(reader)
    if not rows:
        raise ValueError("Jobs file is empty")
    seen = set()
    for row in rows:
        qid, query = row.get("qid"), row.get("query")
        if not qid or not query or not query.strip():
            raise ValueError("Jobs contain an empty qid or query")
        # The original pandas loader infers integer IDs; this release uses canonical FEVER IDs.
        if not qid.isdecimal() or str(int(qid)) != qid:
            raise ValueError("Use canonical decimal FEVER IDs without leading zeroes")
        if qid in seen:
            raise ValueError(f"Duplicate qid {qid}; split combined jobs by condition")
        seen.add(qid)
        if "condition" in row and row["condition"] != condition:
            raise ValueError("Jobs condition differs from CLI condition; use a separate state file")
    return len(rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", required=True, choices=["PRE", "POST", "FILT"])
    for name in ["jobs", "index", "out", "forbidden"]:
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--M", type=int, default=200)
    args = parser.parse_args()
    try:
        count = preflight(args.condition, args.jobs, args.index, args.out, args.forbidden, args.k, args.M)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Run not started: {error}\n")
    command = [sys.executable, str(ORIGINAL), "--condition", args.condition, "--jobs", str(args.jobs),
               "--index", str(args.index), "--out", str(args.out), "--forbidden", str(args.forbidden),
               "--k", str(args.k), "--M", str(args.M)]
    # The original source and actual scientific retrieval path are kept unchanged.
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        parser.exit(completed.returncode, "Original runner failed; any partial output must not be treated as a complete run.\n")
    metadata = {"status": "retrieval only; original runner returned successfully", "condition": args.condition,
                "jobs": count, "k": args.k, "M": args.M, "jobs_sha256": sha(args.jobs),
                "forbidden_sha256": sha(args.forbidden), "original_runner_sha256": sha(ORIGINAL),
                "python": sys.version, "index_directory_name": args.index.name,
                "index_contents_verified": False, "generation_executed": False}
    args.out.with_suffix(args.out.suffix + ".run.json").write_text(json.dumps(metadata, indent=2) + "\n")

if __name__ == "__main__":
    main()
