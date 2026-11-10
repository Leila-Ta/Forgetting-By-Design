# Additional candidate evidence: generation, ranks and score diagnostics

These files extend the initial partial release. Their presence does not establish the paper's final run, detector implementation or statistical denominator.

## The 200-per-kind generation trace

The supplied output archive contains **1,200 nonempty answer records**: 200 Forget and 200 Keep qids in each of PRE/POST/FILT. Both kinds are paired across states, with unchanged qid/query order. Forget inputs are the first 200 rows of the 3,690-query pool; Keep inputs are the first 200 FEVER IDs in the full local Keep mapping. They are not the separate 400-base jobs or 1,000-query sample: only 45 Forget IDs overlap the 1,000 selection.

`data/annotations/generation_200perkind.jsonl` preserves stored score flags, top-k/citation IDs, source-line references and exact query/answer hashes, without publishing answer/claim text. Original text is retained in the author's review materials. The source archive/member hashes and transformations are in `data/annotations/provenance.json`.

| Stored Forget annotation | PRE | POST | FILT |
| --- | ---: | ---: | ---: |
| `leak_strict` true / N_total | 34/200 | 1/200 | 2/200 |
| Percentage from those flags | 17.0 | 0.5 | 1.0 |
| `leak_fuzzy90` true | 105 | 15 | 14 |
| `leak_any` true | 141 | 16 | 15 |
| Nonempty stored citation lists | 128 | 16 | 20 |

The first percentage row matches the published leakage values. This verifies **aggregation of a supplied field**, not its equivalence to the paper's frozen NLI/alias disclosure definition. The original scorer/model revision is absent. Do not choose a different annotation column silently or multiply counts by five.

There is **no abstention flag in this 200-case family**, and no answer exactly equals the paper's INSUFFICIENT_EVIDENCE sentinel. Natural-language refusals occur, but a newly guessed text rule is not the original detector. The separate scorable-count summary reports N_score values and Forget citation counts 128/16/19, whereas these raw stored citation lists number 128/16/20. Without the eligibility/parser code, neither abstention nor final citation coverage is verified from these records.

The file named `stageB_rag_outputs_llama3_8b_with_csr_1000.jsonl` is empty. The file named `...with_csr.jsonl` is a 50-row TODO table, not scored generation. Filenames alone do not establish 1,000 evaluated probes or CSR.

All 150 earlier evidence-swap planning records match answers and top-k lists in this larger 1,200-record file exactly. They remain baseline/planning records: no swapped evidence or post-swap answers have been supplied.

## A separate 20-per-state scored diagnostic

The second archive contains 60 records (20 per state), with source abstention/leakage fields, CSR and some NLI/support debug values. Their retrieved lists match the same qids in the larger generation file, but **all 60 answer strings differ**. Do not join their scores onto the 200-case answers.

The source has 31 literal NaN CSR values, each on a source-labelled abstention with `csr_dbg.reason="abstain"`. NaN is not standard JSON. `diagnostic_20perstate.jsonl` transparently represents those as **null**, with `nonfinite_normalization={"csr":"NaN"}`; no value becomes zero, and all source flags/finite values are preserved. Original nonstandard source bytes remain in the private review area. Only three rows carry NLI leakage-debug probabilities; this is not a supplied runnable evaluator or complete verifier record for the paper.

## Multi-target rank evidence

`data/ranks/forget_multi_target_PRE_POST.tsv` is a byte-identical copy of the combined candidate rank file: 4,160 unique query-target pairs per state, for 3,690 qids and 778 targets. Standalone POST and its duplicate are omitted because the combined file contains that exact subset.

Using the explicit event **any gold target for a query has rank 1–10** reproduces the earlier category means exactly:

| Category | Hit queries / candidate queries |
| --- | ---: |
| crime | 252/271 |
| birth_identity | 2,960/3,209 |
| stigmatised_attribute | 32/39 |
| illness | 132/171 |

The all-one candidate weights yield 3,376/3,690 for that target-hit event. It is not the global any-forbidden-handle exposure event, and does not independently establish the published HWE configuration. The previously different single-target rates are not silently replaced.

`forget_selected_target_FILT.tsv` has 3,690 single selected-target rows, all misses. Its target representation differs from the multi-target PRE/POST file. Do not present these as three identical relevance sets without the original resolver/selection protocol.

`data/scopes/forget_gold_targets_778.txt` is the sorted unique target universe from the combined rank file. It contains both prior masks, and its exact-membership test agrees with all 1,200 stored `cited_forbidden` flags. This is a **diagnostic target set**, not a newly chosen enforcement mask or verified alias closure. The default retrieval examples still explicitly use the pool630 candidate scope. Forget POST/FILT top-k lists in the 200-case trace avoid this target universe, but each has one answer citing a member: clean retrieved IDs do not certify clean citations or disclosure.

## Keep rankings remain incomplete for the published comparison

The new PRE file has 14,310 query-target pairs for 11,090 qids; POST has 135,925 pairs for 106,120 qids. PRE's pair sequence is an exact prefix of POST's pair sequence, but a completeness/evaluability manifest is absent. No matched FILT Keep file is supplied. POST also includes target pages in the revoked target universe, so it is not an already-frozen KeepClean evaluation.

The separate `no_overlap` PRE file covers 65,000 qids with 81,473 rows, one exact duplicate and predominantly lower-case target IDs, unlike the title-cased exports. Case-folding for **diagnostic comparison only** links 10,241 rows to the smaller PRE file; 10,237 target strings differ and 7,195 ranks disagree. No case conversion was applied as a repair. These files remain in the author's candidate review area, not labelled as the published 8,268-control result.

## Reproduce these limited checks

```bash
python3 tools/summarize_candidate_artifacts.py --out work/candidate_annotation_summary.json
```

This operates entirely on bundled annotations/ranks and runs no model. To regenerate the text-free annotations from the two original archives, if available locally:

```bash
python3 tools/prepare_candidate_annotations.py --outputs-zip /path/to/stageB_outputs-20261110T041817Z-1-001.zip --exports-zip /path/to/stageB_exports-20261110T041817Z-1-001.zip --out-dir work/new_annotations
```

The output directory must be new. Rights and provenance review still applies to identifiers/annotations as well as to any later release of raw text.
