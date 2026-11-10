import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any
def load_forbidden(path: str | None) -> Set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"--forbidden not found: {p}")
    return set([ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()])
def safe_mkdir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
def read_done_qids(out_tsv: Path) -> Set[str]:
    if not out_tsv.exists():
        return set()
    done = set()
    with out_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        if "qid" not in r.fieldnames:
            return set()
        for row in r:
            done.add(str(row["qid"]))
    return done
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=["PRE","POST","FILT"])
    ap.add_argument("--jobs", required=True, help="CSV with at least columns: qid, query")
    ap.add_argument("--index", required=True, help="Pyserini BM25 index dir")
    ap.add_argument("--out", required=True, help="Output TSV")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--M", type=int, default=200)
    ap.add_argument("--forbidden", default=None, help="Optional txt: one forbidden docid per line (used for FILT)")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    jobs_path = Path(args.jobs)
    idx_path = Path(args.index)
    out_path = Path(args.out)
    assert jobs_path.exists(), f"Missing jobs file: {jobs_path}"
    assert idx_path.exists(), f"Missing index dir: {idx_path}"
    forbidden = load_forbidden(args.forbidden)
    if args.condition == "FILT" and not forbidden:
      raise ValueError("FILT requires --forbidden (global forbidden docids list).")

    # Pyserini searcher
    try:
        from pyserini.search.lucene import LuceneSearcher
    except Exception as e:
        raise RuntimeError("Pyserini not available. Install/import pyserini in this runtime.") from e
    searcher = LuceneSearcher(str(idx_path))
    done_qids = read_done_qids(out_path) if args.resume else set()
    safe_mkdir(out_path)
    fieldnames = [
        "condition","qid","query",
        "k","M",
        "retrieved_docids_topM",      # pipe-separated
        "retrieved_docids_topk",      # pipe-separated (post-filter if FILT)
        "leakret_at_k",               # 0/1 (any forbidden in top-k) – meaningful for PRE; should be 0 for POST/FILT
        # --- placeholders for your generation pipeline ---
        "answer",
        "citations"                   # pipe-separated or JSON; leave blank if not generating here
    ]
    write_header = not out_path.exists()
    with out_path.open("a", encoding="utf-8", newline="") as fout:
        w = csv.DictWriter(fout, fieldnames=fieldnames, delimiter="\t")
        if write_header:
            w.writeheader()
        import pandas as pd
        jobs = pd.read_csv(jobs_path)
        if "qid" not in jobs.columns or "query" not in jobs.columns:
            raise ValueError(f"Jobs must have columns qid, query. Found: {jobs.columns.tolist()}")
        for i, row in jobs.iterrows():
            qid = str(row["qid"])
            query = str(row["query"])
            if qid in done_qids:
                continue
            hits = searcher.search(query, k=args.M)
            docids = [str(h.docid) for h in hits]
            # Apply FILT at retrieval-time: remove forbidden, then take first k
            if args.condition == "FILT" and forbidden:
                filtered = [d for d in docids if d not in forbidden]
                topk = filtered[:args.k]
            else:
                topk = docids[:args.k]
            # Leakret@k: any forbidden in top-k (for PRE diagnostics; POST/FILT should go to 0)
            leakret = 0
            if forbidden:
                leakret = int(any(d in forbidden for d in topk))
            out_row = {
                "condition": args.condition,
                "qid": qid,
                "query": query,
                "k": args.k,
                "M": args.M,
                "retrieved_docids_topM": "|".join(docids),
                "retrieved_docids_topk": "|".join(topk),
                "leakret_at_k": leakret,
                "answer": "",
                "citations": "",
            }
            # ---- If you want generation in-runner, plug it in here and populate answer/citations ----
            w.writerow(out_row)
            fout.flush()
    print(f"Wrote: {out_path}")
if __name__ == "__main__":
    main()
