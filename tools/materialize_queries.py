"""Recover exact claim text from an independently acquired FEVER JSONL file.

New release utility, not an original experiment/sampling/generation script.
Every required claim must match the SHA-256 in the supplied candidate manifests.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

def read_claims(path, expected):
    found = {}
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            row = json.loads(line)
            qid = str(row["id"])
            if qid not in expected:
                continue
            if qid in found:
                raise ValueError(f"Duplicate required FEVER id {qid} at line {number}")
            claim = row["claim"]
            if not isinstance(claim, str):
                raise ValueError(f"Claim is not text for FEVER id {qid}")
            digest = hashlib.sha256(claim.encode("utf-8")).hexdigest()
            if digest != expected[qid]:
                raise ValueError(f"Claim hash mismatch for FEVER id {qid}; use the matching source")
            found[qid] = claim
    missing = set(expected) - set(found)
    if missing:
        raise ValueError(f"Missing {len(missing)} required FEVER ids, e.g. {sorted(missing)[:5]}")
    return found

def write_table(path, fields, rows, delimiter):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=delimiter, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def materialize(fever, out, root=ROOT):
    if out.exists():
        raise ValueError(f"Output already exists: {out}. Choose a new directory.")
    manifest = root / "data/manifests"
    pool = records(manifest / "forget_pool.jsonl")
    resolved = records(manifest / "forget_resolved.jsonl")
    keep = records(manifest / "keep_person_pairs.jsonl")
    expected = {}
    for row in pool + resolved + keep:
        qid, digest = row["qid"], row["claim_sha256"]
        if qid in expected and expected[qid] != digest:
            raise ValueError(f"Conflicting manifest claim hashes for {qid}")
        expected[qid] = digest
    claims = read_claims(fever, expected)
    pool_map = {row["qid"]: row for row in pool}
    resolved_map = {row["qid"]: row for row in resolved}
    sample_ids = (manifest / "forget_1000.qids").read_text().splitlines()
    robustness_ids = (manifest / "robustness_200.qids").read_text().splitlines()

    def forget_row(row):
        return {"qid": row["qid"], "query": claims[row["qid"]],
                "target_docid": row["target_docid"], "harm_category": row["harm_category"],
                "entity": row["target_docid"]}

    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="fbd-materialize-", dir=out.parent))
    try:
        fields = ["qid", "query", "target_docid", "harm_category", "entity"]
        write_table(stage / "forget_queries.tsv", fields, map(forget_row, pool), "\t")
        write_table(stage / "stageB_forget_1000.tsv", fields,
                    (forget_row(pool_map[q]) for q in sample_ids), "\t")
        for condition in ["PRE", "POST", "FILT"]:
            write_table(stage / f"stageB_jobs_{condition}_1000.csv", ["qid", "query", "condition"],
                        ({"qid": q, "query": claims[q], "condition": condition} for q in sample_ids), ",")
        write_table(stage / "keep_person_only.with_qid.tsv", ["qid", "query", "target_page"],
                    ({"qid": row["qid"], "query": claims[row["qid"]],
                      "target_page": row["target_docid"]} for row in keep), "\t")
        write_table(stage / "forgetset_meta.csv", ["qid", "harm_category", "w"],
                    ({"qid": row["qid"], "harm_category": row["harm_category"], "w": row["w"]} for row in pool), ",")
        for name, selected in [("forget_set_resolved.jsonl", resolved),
                               ("robustness_subset200.jsonl", [resolved_map[q] for q in robustness_ids])]:
            with (stage / name).open("w", encoding="utf-8") as handle:
                for row in selected:
                    handle.write(json.dumps({"id": int(row["qid"]), "query": claims[row["qid"]],
                                             "target_docid": row["target_docid"]}, ensure_ascii=False) + "\n")
        summary = {"status": "claim text recovered by exact hash; no experiment executed",
                   "unique_claims_checked": len(claims), "forget_pool_rows": len(pool),
                   "resolved_rows": len(resolved), "sample_qids": len(sample_ids),
                   "keep_pairs": len(keep), "keep_unique_qids": len({r["qid"] for r in keep}),
                   "format": "UTF-8; LF line endings; semantic records preserved; not original-byte reproduction"}
        (stage / "materialization.json").write_text(json.dumps(summary, indent=2) + "\n")
        os.rename(stage, out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fever", required=True, type=Path, help="Locally downloaded matching FEVER JSONL")
    parser.add_argument("--out-dir", required=True, type=Path, help="New output directory; never overwritten")
    args = parser.parse_args()
    try:
        result = materialize(args.fever, args.out_dir)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"Cannot materialize data: {error}\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
