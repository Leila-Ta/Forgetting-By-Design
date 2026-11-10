# Result provenance

- **`published_report_card.csv`**: manually transcribed Table 5 from the published paper, including its printed intervals. Source: Tavakoli and Sanderson (2026), DOI [10.1145/3805712.3808545](https://doi.org/10.1145/3805712.3808545), Table 5, p. 2730. The paper displays CC BY 4.0. This transcription is not a rerun, and no numerical corrections have been applied. Leakage N=1,000 and utility N=8,268 are reported in the paper; original abstention/citation counters remain unverified.
- **`offline_audit_pool630.json` / `offline_audit_resolved605.json`**: actually computed from the supplied three-state retrieval TSVs and named masks, using `tools/audit_retrieval_exports.py`. Source-file hashes are recorded. They show list-level exposure and scope sensitivity; they are not answer leakage or Table-5 reproduction. Their source TSVs are not in the initial public folder.
- **`software_validation.json`**: executed release-tool checks, including 16 passing regression tests and semantic round-trips for nine generated views using 13,545 supplied claim texts. A fresh upstream source, real Pyserini, model inference and full CFF schema validation were not tested.

- **`candidate_annotation_summary.json`**: actually computed from bundled candidate annotations and multi-target ranks by `tools/summarize_candidate_artifacts.py`. It re-aggregates stored 200-case flags and separate 20-case diagnostic scores, and counts per-query gold-target hits. It does not implement the original detector or infer missing abstention labels.

No CI, model run, significance test, confidence interval or experimental success is implied beyond the explicitly recorded checks.
