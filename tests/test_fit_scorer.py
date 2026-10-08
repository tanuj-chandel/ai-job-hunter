"""
Smoke tests for job title fit scorer and tier assignments.
"""
import unittest
from easy_apply_scraper import fit_score

class TestFitScorer(unittest.TestCase):
    def test_ten_sample_titles_tier_assignments(self):
        sample_jobs = [
            # High Fit (score >= 85)
            ("Senior AI Evaluator", "High"),
            ("LLM Prompt Engineer", "High"),
            ("RLHF Specialist", "High"),
            ("Operations Lead", "High"),

            # Medium Fit (70 <= score < 85)
            ("Machine Learning Data Labeler", "Medium"),
            ("NLP Content Moderator", "Medium"),
            ("Search Quality Rater", "Medium"),
            ("Process Improvement Analyst", "Medium"),

            # Low Fit / Disqualified (score == 0)
            ("Delivery Driver", "Low"),
            ("Warehouse Forklift Operator", "Low"),
        ]

        self.assertEqual(len(sample_jobs), 10, "Must test exactly 10 sample titles.")

        for title, expected_tier in sample_jobs:
            with self.subTest(title=title, expected_tier=expected_tier):
                score = fit_score(title)
                if expected_tier == "High":
                    self.assertGreaterEqual(score, 85, f"Expected High fit (>=85) for '{title}', got {score}")
                elif expected_tier == "Medium":
                    self.assertGreaterEqual(score, 70, f"Expected Medium fit (>=70) for '{title}', got {score}")
                    self.assertLess(score, 85, f"Expected Medium fit (<85) for '{title}', got {score}")
                elif expected_tier == "Low":
                    self.assertEqual(score, 0, f"Expected Disqualified (0) for '{title}', got {score}")

if __name__ == "__main__":
    unittest.main()
