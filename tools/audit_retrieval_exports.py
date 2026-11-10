"""Recompute exact-ID exposure from existing TSVs; does not run retrieval/models."""
from pathlib import Path
import argparse
import csv
import hashlib
import json

def read_export(path, condition):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        needed = {"qid", "query", "condition", "k", "M", "retrieved_docids_topM", "retrieved_docids_topk", "leakret_at_k"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing columns in {path.name}")
        rows = list(reader)
    if not rows or len({r["qid"] for r in rows}) != len(rows):
        raise ValueError("Require a nonempty export with unique qids")
    for row in rows:
        if row["condition"] != condition or int(row["M"]) < int(row["k"]) or int(row["k"]) < 1:
            raise ValueError("Invalid condition/k/M in export")
        if row["leakret_at_k"] not in {"0", "1"}:
            raise ValueError("Stored exposure flag must be 0 or 1")
    return rows

def docids(row, field):
    return row[field].split("|") if row[field] else []

def audit(paths, mask_path):
    mask = set(mask_path.read_text(encoding="utf-8").splitlines())
    if not mask or "" in mask:
        raise ValueError("Require nonempty exact forbidden IDs without blank lines")
    data = {state: read_export(path, state) for state, path in paths.items()}
    pre_pairs = [(r["qid"], r["query"]) for r in data["PRE"]]
    if any([(r["qid"], r["query"]) for r in rows] != pre_pairs for rows in data.values()):
        raise ValueError("Exports must have identical ordered qid/query pairs")
    result = {"verification": "offline recomputation from supplied lists; no retrieval, generation or published result reproduced",
              "mask_file": mask_path.name, "mask_size": len(mask),
              "mask_sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest(), "states": {}}
    for state, rows in data.items():
        exposed = [bool(set(docids(r, "retrieved_docids_topk")) & mask) for r in rows]
        result["states"][state] = {"queries": len(rows), "served_exposure_count": sum(exposed),
            "served_exposure_rate": sum(exposed) / len(rows),
            "stored_flag_disagreements": sum(int(r["leakret_at_k"]) != int(flag) for r, flag in zip(rows, exposed)),
            "shortfall_query_count": sum(len(docids(r, "retrieved_docids_topk")) < int(r["k"]) for r in rows),
            "nonempty_answer_cells": sum(bool(r.get("answer", "").strip()) for r in rows),
            "nonempty_citation_cells": sum(bool(r.get("citations", "").strip()) for r in rows),
            "source_sha256": hashlib.sha256(paths[state].read_bytes()).hexdigest()}
    result["PRE_FILT_identical_raw_lists"] = sum(a["retrieved_docids_topM"] == b["retrieved_docids_topM"]
                                                   for a, b in zip(data["PRE"], data["FILT"]))
    result["FILT_filter_transformation_matches"] = sum(
        [d for d in docids(r, "retrieved_docids_topM") if d not in mask][:int(r["k"])] == docids(r, "retrieved_docids_topk")
        for r in data["FILT"])
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for state in ["pre", "post", "filt"]:
        parser.add_argument("--" + state, required=True, type=Path)
    parser.add_argument("--mask", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.out and args.out.exists():
        parser.exit(2, "Output exists; choose a new file.\n")
    try:
        result = audit({s: getattr(args, s.lower()) for s in ["PRE", "POST", "FILT"]}, args.mask)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"Cannot audit exports: {error}\n")
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")

if __name__ == "__main__":
    main()
