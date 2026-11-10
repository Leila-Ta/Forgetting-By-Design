# Forgetting-by-Design: auditing RAG for selective forgetting

Research materials for **Leila Tavakoli and Mark Sanderson**, *Deletion Isn’t Enough: Auditing RAG for Selective Forgetting*, SIGIR 2026 Perspectives, pp. 2721–2733. [Published paper / DOI](https://doi.org/10.1145/3805712.3808545).

**Release status: partial research artefact release.** This repository contains the supplied retrieval runner, candidate identifier manifests, claim-reconstruction utilities and explicit verification records. It does **not yet reproduce the paper end to end**: generation/evaluation code, the frozen 8,268-control evaluation, complete original answer traces, corpus/index construction and the original environment are missing. Candidate manifests differ in target assignment and have not been certified as the published run. See [known issues](docs/known_issues.md) and [licensing](LICENSING.md).

## Research contribution

Forgetting-by-Design (FBD) is a mechanism-agnostic, black-box audit specification. It separates record-scoped enforcement from proposition-scoped non-disclosure, checking whether revoked information is still disclosed while lawful utility and attribution remain usable. It is an audit protocol, not an unlearning mechanism or a compliance certificate.

The paired protocol compares fixed queries across:

- **PRE:** the baseline system.
- **POST:** hard deletion followed by re-indexing.
- **FILT:** retrieval filtering with rank filling, or explicitly reported shortfall.

The paper's illustrative stack uses FEVER/Wikipedia, BM25, LLaMA-3-8B-Instruct and a frozen NLI verifier with threshold 0.80. The supplied script implements **retrieval only**. It does not create a POST index, run a language model or implement the answer-level metrics.

## Published reference values

These values are transcribed from Table 5, not newly computed results.

| Metric (%) | PRE | POST | FILT |
| --- | ---: | ---: | ---: |
| Answer leakage | 17.0 | 0.5 | 1.0 |
| Abstention | 12.0 | 26.5 | 27.0 |
| Citation coverage | 64.0 | 8.0 | 9.5 |
| KeepClean MRR@10 | 52.3 | 52.7 | 40.4 |
| Relative MRR penalty | — | −0.75 | 22.7 |

The paper reports 1,000 revoked probes for leakage and 8,268 KeepClean controls for utility. [The reference CSV](results/published_report_card.csv) preserves the printed intervals. The available 200-case scoring summary, citation denominator and interval provenance require reconciliation; see [known issues](docs/known_issues.md). Do not treat this table or its CSV as evidence of a successful rerun.

## Repository contents

| Path | Purpose |
| --- | --- |
| `scripts/original/run_stageB.py` | Byte-identical supplied retrieval script |
| `tools/run_retrieval.py` | New input/output guards around that script; ranking/filtering unchanged |
| `data/manifests/` | Candidate FEVER IDs, targets, annotations and exact claim hashes; no claim/answer text |
| `data/scopes/` | Separate 630-ID pool and 605-ID resolved scopes; not interchangeable |
| `tools/materialize_queries.py` | Recover matching query text from a locally acquired FEVER file |
| `tools/audit_retrieval_exports.py` | Recompute exact-ID exposure from existing retrieval TSVs |
| `tools/verify_release.py` | Check file hashes and manifest relationships |
| `configs/retrieval_recorded.json` | Observed k=10/M=200; unknown original settings explicitly null |
| `results/` | Published reference table, labelled offline audits and actual software-validation record |
| `docs/reproduction.md` | Commands, requirements and component-level reproduction status |
| `tests/` | Regression checks for release-tool failure modes; no model tests |

No model weights, corpus dump, binary index, claim text or full answer/retrieval traces are bundled. The supplied index was incomplete and is not a usable download asset.

## Installation and quick verification

The release tools and tests require **Python 3.10+** and use its standard library. They were checked with Python 3.12.14; this is not the original experiment environment. From the repository root:

```bash
python3 tools/verify_release.py
python3 -m unittest discover -s tests -v
```

These commands need no GPU or Pyserini and validate the package, not the published experiments.

For query reconstruction, obtain the matching FEVER JSONL through the [official dataset page](https://fever.ai/dataset/fever.html), following its terms. Then:

```bash
python3 tools/materialize_queries.py --fever /path/to/train.jsonl --out-dir work/data
```

The tool requires every selected claim to match its exact UTF-8 SHA-256 and refuses missing/changed claims and existing output directories. It uses frozen ID lists and does not resample or infer a seed. See [data provenance](data/README.md).

Retrieval additionally requires the original compatible Pyserini/pandas/Java environment and complete indices. Versions, BM25 parameters and the corpus recipe have not been recovered. `requirements-retrieval.in` is a dependency inventory, **not a validated lockfile**. Do not assume installing current packages reproduces the original stack. [Execution details](docs/reproduction.md).

## Verification performed

Eleven regression tests passed. Claim materialization was checked against **13,545 unique claim strings from the supplied source files**, with nine semantic record round-trips. The original retrieval script's bytes were preserved. Existing ranked-list exposure was recomputed under each named mask. A fresh upstream FEVER download, real BM25, generation, NLI and Table-5 reproduction were **not** run. [Machine-readable record](results/software_validation.json).

## Citation and terms

Use [CITATION.cff](CITATION.cff) or [paper.bib](paper.bib) to cite the published paper; cite FEVER where its data is used. The citation authors describe the paper and are not a declaration of ownership of every artefact. Software ownership/licensing and upstream data terms remain separate: [LICENSING.md](LICENSING.md).
