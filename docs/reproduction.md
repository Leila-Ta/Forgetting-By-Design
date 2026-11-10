# Reproduction scope and commands

This release can validate its own files and recover candidate query inputs. It cannot yet regenerate the published answer metrics or lawful-utility results.

| Component | Available material | Execution status / blocker |
| --- | --- | --- |
| Bundled artefacts | Hash list and queryless manifests | File checks and relationships verified |
| Query input recovery | Frozen IDs, targets and exact claim hashes | Nine semantic round-trips verified using supplied claim text; upstream download untested |
| Retrieval/filter logic | Unmodified supplied script and separate guard launcher | Original control flow inspected/tested with simulated search; real Pyserini not run |
| Supplied retrieval audits | Public aggregate audit JSONs; auditing utility | Computed from author-supplied TSVs; raw TSVs are not bundled publicly |
| Table 5 leakage/abstention/CiteCov | Printed reference CSV; partial count/answer evidence retained by author | Full generation, scorer, counters and run identity missing |
| Table 5 KeepClean MRR/SR | Printed reference CSV; candidate Keep views | Frozen 8,268 controls/relevance/ranks and unrounded aggregates missing |
| ALR/CSR/USCR | Paper specification | Context/citation/support implementation and traces missing |
| HWE | Candidate uniform weights/categories; separate category summary | Indicator and producing code/run unresolved |
| Neutral AR-ES | Partial baseline/planning jobs retained by author | Actual replacements, post-swap answers and equivalence scorer missing |
| Figure 1 / Table 1 | Conceptual paper content | Not numerical experiments requiring a fabricated reproduction script |

## Commands that work without models or an index

From the repository root, Python 3.10+:

```bash
python3 tools/verify_release.py
python3 -m unittest discover -s tests -v
python3 tools/materialize_queries.py --fever /path/to/matching-fever.jsonl --out-dir work/data
```

The first two are package/software checks. The third needs the matching external FEVER claim source. See `results/software_validation.json` for exactly what was executed during preparation.

## Conditional retrieval execution

The following are execution templates for the supplied retrieval program, **not verified published-reproduction commands**. Before using them, recover a compatible pinned Pyserini/pandas/Java environment, BM25/analyser settings and complete PRE/POST indices. The archive originally supplied is missing `_4.fdt` and `_6.fdt`; do not use it as a complete index. No indexing/deletion implementation is supplied here. `requirements-retrieval.in` lists imports without inventing version pins.

After materialization, in the recovered environment:

```bash
python3 tools/run_retrieval.py --condition PRE --jobs work/data/stageB_jobs_PRE_1000.csv --index /path/to/complete_PRE_index --forbidden data/scopes/pool_630.txt --out work/runs/PRE.tsv --k 10 --M 200
python3 tools/run_retrieval.py --condition POST --jobs work/data/stageB_jobs_POST_1000.csv --index /path/to/complete_POST_index --forbidden data/scopes/pool_630.txt --out work/runs/POST.tsv --k 10 --M 200
python3 tools/run_retrieval.py --condition FILT --jobs work/data/stageB_jobs_FILT_1000.csv --index /path/to/complete_PRE_index --forbidden data/scopes/pool_630.txt --out work/runs/FILT.tsv --k 10 --M 200
```

These templates explicitly use the **pool scope**, consistent with the supplied pool-job filtering transformation. This is not an author-approved choice of the paper's final policy scope. To investigate the alternative resolved scope, use a separate run/output and explicitly name `resolved_605.txt`; do not merge scopes or reuse run labels silently.

The launcher rejects missing masks, duplicate qids, mixed/wrong conditions, M<k and existing outputs. It invokes the original script without changing ranking/filtering. It does not enable that script's unsafe append/resume route. The added `.run.json` records source/mask hashes but does not certify the index contents or recover unknown scientific settings. Search may fill fewer than k from the finite M pool; no further retrieval is invented.

Answers and citations are blank placeholders in this program. A successful retrieval command does not execute Llama, NLI, abstention detection, citation support or forgetting at the answer level.

## Audit existing exports

With appropriately licensed three-state exports available locally:

```bash
python3 tools/audit_retrieval_exports.py --pre /path/to/PRE.tsv --post /path/to/POST.tsv --filt /path/to/FILT.tsv --mask data/scopes/pool_630.txt --out work/audit_pool630.json
python3 tools/audit_retrieval_exports.py --pre /path/to/PRE.tsv --post /path/to/POST.tsv --filt /path/to/FILT.tsv --mask data/scopes/resolved_605.txt --out work/audit_resolved605.json
```

The utility uses exact docid membership, checks pairing and recomputes the recorded-list event instead of trusting the stored flag. The public aggregate JSONs include hashes of their three source TSVs. They were computed from supplied data, with no new search/model calls. The raw source exports remain outside the initial public folder pending provenance/licensing review.

## Reproducing the paper's main table

There is no complete command yet. `results/published_report_card.csv` is a faithful transcription, not a computed output. Recover the missing generation/evaluation code, original prompts/roles/context/decoding, model/verifier revisions, frozen control split, full outputs, denominator logic and table-producing inputs before claiming reproduction. Do not use the materializer, TODO tables or the 200-case summary as substitutes for those components.
