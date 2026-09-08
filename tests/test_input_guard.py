"""Canonical tests for Cross Clinical educational input guards."""

from __future__ import annotations

import unittest

from input_guard import REFUSAL_CLINICAL, REFUSAL_PHI, guard_input


class TestInputGuard(unittest.TestCase):
    def test_clean_input_passes(self) -> None:
        self.assertIsNone(guard_input("explain hypertension for my study guide"))

    def test_phi_mrn_blocked(self) -> None:
        self.assertEqual(guard_input("patient MRN 12345"), REFUSAL_PHI)

    def test_phi_ssn_blocked(self) -> None:
        self.assertEqual(guard_input("SSN 123-45-6789"), REFUSAL_PHI)

    def test_phi_patient_name_blocked(self) -> None:
        self.assertEqual(guard_input("patient named John Smith"), REFUSAL_PHI)

    def test_diagnosis_blocked(self) -> None:
        self.assertEqual(guard_input("diagnose my symptoms"), REFUSAL_CLINICAL)

    def test_prescribe_blocked(self) -> None:
        self.assertEqual(guard_input("what should I prescribe"), REFUSAL_CLINICAL)


if __name__ == "__main__":
    unittest.main()
