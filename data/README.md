# Candidate data manifests and provenance

These are deterministically derived views and annotations of supplied research files, not a new benchmark or verified publication split. They contain IDs, document-title handles, candidate harm annotations, weights and claim hashes. Claim text and generated answer strings are deliberately acquired/handled separately. SHA-256 hashes provide identity checks, not anonymity or a privacy guarantee.

| Manifest | Records | Source and meaning |
| --- | ---: | --- |
| `manifests/forget_pool.jsonl` | 3,690 | Full candidate Forget qids/targets/categories; 630 targets; supplied w=1.0 |
| `manifests/forget_resolved.jsonl` | 3,542 | Distinct resolved target view; 605 targets; 41 shared target assignments differ |
| `manifests/forget_1000.qids` | 1,000 | Ordered selection from the pool view, matching supplied retrieval jobs |
| `manifests/robustness_200.qids` | 200 | Ordered selection from the resolved view; matches 800 original family prompts |
| `manifests/keep_person_pairs.jsonl` | 10,140 | Unique query-target pairs for 9,855 FEVER IDs and 676 target pages |
| `scopes/pool_630.txt` | 630 | Exact supplied pool handles |
| `scopes/resolved_605.txt` | 605 | Exact supplied resolved-target handles |
| `scopes/forget_gold_targets_778.txt` | 778 | Derived unique gold-target universe; diagnostic only, not a new enforcement choice |
| `annotations/generation_200perkind.jsonl` | 1,200 | Stored 200-per-kind/state flags, handles and text hashes; no original abstention labels |
| `annotations/diagnostic_20perstate.jsonl` | 60 | Separate scored diagnostic; undefined CSR values explicitly null-marked |
| `ranks/forget_multi_target_PRE_POST.tsv` | 8,320 | 4,160 query-target rows per state for the same 3,690 qids |
| `ranks/forget_selected_target_FILT.tsv` | 3,690 | Single selected-target FILT view; not identical relevance representation |

Every `qid` here is a **FEVER claim ID represented as a decimal string**. The original local Keep ordinals and page-list numbers are not used as query IDs in these views. Keep repeated qids preserve multiple target pages and must not be deduplicated by qid alone.

The two candidate enforcement scopes share 591 IDs; 39 are pool-only and 14 resolved-only. The larger list is not a superset. The Keep targets have no exact-string overlap with either scope, but this does not prove full alias closure or identify the published 8,268 controls. No targets were corrected or merged to conceal these differences.

`manifest_provenance.json` records original filenames/hashes, transformations and counts. New manifests preserve source row order and exact target strings; they omit claim text and retain its SHA-256. The original raw sources have not been silently replaced or relabelled.

Annotation source/transform metadata is in `annotations/provenance.json`; [additional evidence](../docs/additional_artifacts.md) explains cohort sizes, score-field limits and explicit NaN-to-null handling. Generation flags are supplied annotations, not re-executed NLI decisions. No abstention labels are inferred for that trace.

## Recovering query text

1. Acquire the matching FEVER claim JSONL using the [official FEVER download page](https://fever.ai/dataset/fever.html). The upstream training data is a candidate source, not a newly verified corpus identity.
2. Read the [upstream data notice](https://fever.ai/download/fever/license.html) and [repository terms](../LICENSING.md).
3. Run `python3 tools/materialize_queries.py --fever /path/to/train.jsonl --out-dir work/data` from the repository root.

The tool requires all **13,545 unique claims** used by the pool/resolved/person-Keep query manifests. The separate generation annotations are not additional query-manifest inputs, and this tool does not reconstruct answers or scores. Hash mismatches or missing IDs stop the operation. It does not download data or silently use another version. Output uses UTF-8/LF and preserves semantic records; byte identity to original CRLF/JSON formatting is not claimed. It reconstructs the three separate 1,000-query jobs, full pool, resolved view, robustness subset, Keep pairs and weight metadata.

The materializer was tested using claim texts already supplied by the author, wrapped temporarily in the FEVER `id`/`claim` format. It was **not tested against a fresh upstream download**. If upstream text fails a hash check, recover the original matching source; do not bypass the check.

## Interpretation and rights

FEVER includes altered claims with SUPPORTS, REFUTES and NOT ENOUGH INFO labels. A query string, a target title or a hypothetical harm annotation is not a verified biographical fact, a legal assessment or a real erasure request. Full labels/evidence and fixed prohibited propositions remain necessary for answer-level evaluation.

Upstream FEVER/Wikipedia terms govern relevant source material; original annotation ownership and redistribution conditions still require author review. No blanket MIT or CC licence for every file is asserted. Public availability of a source is not itself the licensing review. See [LICENSING.md](../LICENSING.md).
