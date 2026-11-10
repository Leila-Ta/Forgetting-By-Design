from pathlib import Path
import importlib.util
import math
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

prepare = load("prepare_candidate_annotations")
summary = load("summarize_candidate_artifacts")

class CandidateAnnotationTests(unittest.TestCase):
    def diagnostic(self):
        return dict(qid="101", condition="I_pre", query="example", answer="reply", forbidden_fact="example",
                    k=10, retrieved_docids=[], leak_ret=0, abstain=1, leak_ans=0, leak_dbg={"reason": "abstain"},
                    alr=0, csr=math.nan, csr_dbg={"reason": "abstain"})

    def test_abstention_nan_becomes_explicit_null_not_zero(self):
        row = prepare.diagnostic_annotation(self.diagnostic(), 1)
        self.assertIsNone(row["csr"])
        self.assertEqual(row["nonfinite_normalization"], {"csr": "NaN"})
        self.assertEqual(row["abstain"], 1)

    def test_unexpected_nonfinite_metric_not_silently_changed(self):
        row = self.diagnostic()
        row["abstain"] = 0
        with self.assertRaises(ValueError):
            prepare.diagnostic_annotation(row, 1)

    def generation(self):
        return dict(qid="101", kind="forget", condition="PRE", cited_docids=[], cited_forbidden=False,
                    answer_is_exact_INSUFFICIENT_EVIDENCE=False, leak_strict=True, leak_fuzzy90=False, leak_any=True)

    def test_flags_reaggregated_without_invented_abstention_metric(self):
        result = summary.generation_summary([self.generation()], set())[0]
        self.assertEqual(result["stored_leak_strict_count"], 1)
        self.assertNotIn("abstention_pct", result)
        self.assertIn("not computed", result["abstention_metric_status"])

    def test_duplicate_state_record_refused(self):
        with self.assertRaises(ValueError):
            summary.generation_summary([self.generation(), self.generation()], set())

    def test_multi_target_hits_count_once_per_query(self):
        pool = [dict(qid="101", harm_category="example", w=1.0), dict(qid="102", harm_category="example", w=1.0)]
        ranks = [dict(qid="101", index_flag="PRE", rank="1"), dict(qid="101", index_flag="PRE", rank="2"),
                 dict(qid="102", index_flag="PRE", rank="0")]
        result = summary.target_hit_summary(pool, ranks)[0]
        self.assertEqual(result["any_gold_target_hit_count"], 1)
        self.assertEqual(result["N_queries"], 2)
        self.assertEqual(result["weighted_target_hit_rate"], 0.5)

if __name__ == "__main__":
    unittest.main()
