"""
Test for 'Real Applied only on confirmation' verification logic using HTML fixtures.
"""
import os
import unittest
from browser_apply_agent import is_confirmed_submission

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

class TestConfirmationVerifier(unittest.TestCase):
    def setUp(self):
        self.confirmed_html_path = os.path.join(FIXTURES_DIR, "naukri_confirmed.html")
        self.unconfirmed_html_path = os.path.join(FIXTURES_DIR, "naukri_unconfirmed.html")
        self.assertTrue(os.path.exists(self.confirmed_html_path), "Confirmed HTML fixture must exist.")
        self.assertTrue(os.path.exists(self.unconfirmed_html_path), "Unconfirmed HTML fixture must exist.")

    def test_confirmed_html_fixture_detected(self):
        with open(self.confirmed_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        is_confirmed = is_confirmed_submission(html_content)
        self.assertTrue(is_confirmed, "Confirmed fixture must satisfy confirmation keywords.")

        # Real Applied status is assigned ONLY when confirmed is True
        resulting_status = "Real Applied" if is_confirmed else "Attempted"
        self.assertEqual(resulting_status, "Real Applied")

    def test_unconfirmed_html_fixture_not_marked_applied(self):
        with open(self.unconfirmed_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        is_confirmed = is_confirmed_submission(html_content)
        self.assertFalse(is_confirmed, "Unconfirmed fixture must NOT trigger confirmation keywords.")

        # Guardrail: Must stay Attempted, never prematurely marked 'Real Applied'
        resulting_status = "Real Applied" if is_confirmed else "Attempted"
        self.assertEqual(resulting_status, "Attempted")
        self.assertNotEqual(resulting_status, "Real Applied")

if __name__ == "__main__":
    unittest.main()
