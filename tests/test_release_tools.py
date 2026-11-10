"""Regression checks for observed input/output hazards, not model experiments."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

runner = load("run_retrieval")
materializer = load("materialize_queries")
auditor = load("audit_retrieval_exports")

class ReleaseToolChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.index = self.path / "index"
        self.index.mkdir()
        self.jobs = self.path / "jobs.csv"
        self.jobs.write_text("qid,query,condition\n101,example,PRE\n")
        self.mask = self.path / "mask.txt"
        self.mask.write_text("blocked\n")
        self.out = self.path / "out.tsv"

    def tearDown(self):
        self.temp.cleanup()

    def preflight(self, **kwargs):
        args = dict(condition="PRE", jobs=self.jobs, index=self.index, out=self.out,
                    forbidden=self.mask, k=1, M=2)
        args.update(kwargs)
        return runner.preflight(**args)

    def test_valid_single_condition_job(self):
        self.assertEqual(self.preflight(), 1)

    def test_combined_condition_jobs_rejected(self):
        self.jobs.write_text("qid,query,condition\n101,example,PRE\n101,example,POST\n")
        with self.assertRaises(ValueError):
            self.preflight()

    def test_wrong_condition_rejected(self):
        with self.assertRaises(ValueError):
            self.preflight(condition="POST")

    def test_existing_output_not_appended(self):
        self.out.write_text("previous run\n")
        with self.assertRaises(ValueError):
            self.preflight()
        self.assertEqual(self.out.read_text(), "previous run\n")

    def test_missing_mask_not_scored_as_zero(self):
        self.mask.unlink()
        with self.assertRaises(ValueError):
            self.preflight()

    def test_candidate_depth_must_cover_k(self):
        with self.assertRaises(ValueError):
            self.preflight(k=3, M=2)

    def claim_file(self, rows):
        path = self.path / "fever.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return path

    def test_exact_claim_hash(self):
        path = self.claim_file([{"id": 101, "claim": "exact claim"}])
        digest = hashlib.sha256(b"exact claim").hexdigest()
        self.assertEqual(materializer.read_claims(path, {"101": digest}), {"101": "exact claim"})

    def test_changed_claim_refused(self):
        path = self.claim_file([{"id": 101, "claim": "changed claim"}])
        with self.assertRaises(ValueError):
            materializer.read_claims(path, {"101": hashlib.sha256(b"original claim").hexdigest()})

    def test_missing_claim_refused(self):
        path = self.claim_file([])
        with self.assertRaises(ValueError):
            materializer.read_claims(path, {"101": "0" * 64})

    def test_duplicate_source_id_refused(self):
        path = self.claim_file([{"id": 101, "claim": "exact"}, {"id": 101, "claim": "exact"}])
        with self.assertRaises(ValueError):
            materializer.read_claims(path, {"101": hashlib.sha256(b"exact").hexdigest()})

    def test_exposure_recomputed_instead_of_trusting_zero_flag(self):
        paths = {}
        fields = ["condition", "qid", "query", "k", "M", "retrieved_docids_topM",
                  "retrieved_docids_topk", "leakret_at_k", "answer", "citations"]
        for state in ["PRE", "POST", "FILT"]:
            path = self.path / (state + ".tsv")
            raw = "blocked|allowed" if state != "POST" else "allowed|other"
            served = "blocked" if state == "PRE" else "allowed"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
                writer.writeheader()
                writer.writerow(dict(zip(fields, [state, "101", "example", 1, 2, raw, served, 0, "", ""])))
            paths[state] = path
        report = auditor.audit(paths, self.mask)
        self.assertEqual(report["states"]["PRE"]["served_exposure_count"], 1)
        self.assertEqual(report["states"]["PRE"]["stored_flag_disagreements"], 1)
        self.assertEqual(report["states"]["FILT"]["served_exposure_count"], 0)
        self.assertEqual(report["FILT_filter_transformation_matches"], 1)

if __name__ == "__main__":
    unittest.main()
