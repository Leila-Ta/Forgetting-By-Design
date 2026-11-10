"""Prepare query/answer-text-free annotations from two supplied candidate ZIPs.

No detector is run. Original score fields are retained as supplied. In the
separate 20-case diagnostic only, CSR NaN on source-labelled abstentions is
represented by JSON null with an explicit original-notation marker.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import shutil
import tempfile
import zipfile

MAIN_MEMBER = "stageB_outputs/stageB_rag_outputs_llama3_8b.jsonl"
DIAGNOSTIC_MEMBER = "stageB_exports/stageB_forget_llama3_bm25_2.jsonl"
STATES = {"I_pre": "PRE", "I_post_minus_forget": "POST", "I_pre_plus_filter": "FILT"}

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main_annotation(row, line):
    result = {"qid": str(row["qid"]), "kind": row["kind"], "condition": row["condition"],
              "source_line": line, "query_sha256": digest(row["query"]), "answer_sha256": digest(row["answer"]),
              "answer_is_exact_INSUFFICIENT_EVIDENCE": row["answer"].strip() == "INSUFFICIENT_EVIDENCE"}
    for name in ["topk_docids", "cited_docids", "cited_forbidden", "leak_strict", "leak_fuzzy90", "leak_any",
                 "keep_targets_auditable", "retrieved_target", "cites_target"]:
        if name in row:
            result[name] = row[name]
    if "forbidden_fact" in row:
        result["forbidden_fact_sha256"] = digest(row["forbidden_fact"])
    return result

def diagnostic_annotation(row, line):
    result = {"qid": str(row["qid"]), "source_condition": row["condition"],
              "condition": STATES[row["condition"]], "source_line": line,
              "query_sha256": digest(row["query"]), "answer_sha256": digest(row["answer"]),
              "forbidden_fact_sha256": digest(row["forbidden_fact"])}
    for name in ["k", "retrieved_docids", "leak_ret", "abstain", "leak_ans", "leak_dbg", "alr", "csr", "csr_dbg"]:
        result[name] = row[name]
    result["nonfinite_normalization"] = {}
    if isinstance(result["csr"], float) and not math.isfinite(result["csr"]):
        if not (math.isnan(result["csr"]) and row["abstain"] == 1 and row["csr_dbg"].get("reason") == "abstain"):
            raise ValueError("Unexpected nonfinite CSR; no conversion was authorised by this data rule")
        result["csr"] = None
        result["nonfinite_normalization"] = {"csr": "NaN"}
    # Fail rather than silently changing any other non-standard numeric value.
    json.dumps(result, allow_nan=False)
    return result

def member(path, name):
    with zipfile.ZipFile(path) as archive:
        if archive.namelist().count(name) != 1:
            raise ValueError(f"Require exactly one member named {name}")
        info = archive.getinfo(name)
        if info.file_size > 10 * 1024 * 1024 or info.flag_bits & 1:
            raise ValueError("Unexpected member size/encryption")
        return archive.read(name)

def prepare(outputs_zip, exports_zip, out):
    if out.exists():
        raise ValueError("Output exists; use a new directory")
    main_bytes = member(outputs_zip, MAIN_MEMBER)
    diag_bytes = member(exports_zip, DIAGNOSTIC_MEMBER)
    main = [main_annotation(json.loads(line), i) for i, line in enumerate(main_bytes.decode("utf-8").splitlines(), 1)]
    diagnostic = [diagnostic_annotation(json.loads(line), i) for i, line in enumerate(diag_bytes.decode("utf-8").splitlines(), 1)]
    sources = [{"archive": path.name, "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "member": name, "member_sha256": hashlib.sha256(data).hexdigest(), "member_bytes": len(data)}
               for path, name, data in [(outputs_zip, MAIN_MEMBER, main_bytes), (exports_zip, DIAGNOSTIC_MEMBER, diag_bytes)]]
    provenance = {"status": "candidate supplied annotations; detectors not rerun; not the verified published run",
                  "sources": sources, "generation_records": len(main), "diagnostic_records": len(diagnostic),
                  "transformations": ["Remove query, answer and forbidden-fact strings; retain their exact UTF-8 SHA-256",
                                      "Represent qids as decimal strings and retain source line numbers",
                                      "Map diagnostic condition labels explicitly while retaining source_condition",
                                      "CSR NaN on source-labelled abstentions becomes null with original NaN notation; never zero"],
                  "diagnostic_CSR_null_normalizations": sum(bool(r["nonfinite_normalization"]) for r in diagnostic),
                  "original_scoring_code_available": False,
                  "generation_abstention_labels_available": False}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="fbd-annotations-", dir=out.parent))
    try:
        for filename, rows in [("generation_200perkind.jsonl", main), ("diagnostic_20perstate.jsonl", diagnostic)]:
            (stage / filename).write_text("".join(json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8")
        (stage / "provenance.json").write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n")
        os.rename(stage, out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return provenance

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs-zip", type=Path, required=True)
    parser.add_argument("--exports-zip", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.outputs_zip, args.exports_zip, args.out_dir)
    except (KeyError, ValueError, OSError, zipfile.BadZipFile) as error:
        parser.exit(2, f"Annotations not prepared: {error}\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
