from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe

from qd_hrms.performance import (
	PIP_RATING_BANDS,
	_parse_reviewers,
	apply_rating_band,
	rating_band_for_score,
	validate_performance_feedback,
)


DEFAULT_LEVELS = [
	{"score": 1, "label": "Unsatisfactory"},
	{"score": 2, "label": "Needs Improvement"},
	{"score": 3, "label": "Meets Expectations"},
	{"score": 4, "label": "Exceeds Expectations"},
	{"score": 5, "label": "Outstanding"},
]


class TestPerformanceScoring(TestCase):
	def test_nearest_rating_band(self):
		self.assertEqual(rating_band_for_score(1.2, DEFAULT_LEVELS), "Unsatisfactory")
		self.assertEqual(rating_band_for_score(2.4, DEFAULT_LEVELS), "Needs Improvement")
		self.assertEqual(rating_band_for_score(3.0, DEFAULT_LEVELS), "Meets Expectations")
		self.assertEqual(rating_band_for_score(4.6, DEFAULT_LEVELS), "Outstanding")

	def test_empty_scale_returns_none(self):
		self.assertIsNone(rating_band_for_score(3, []))

	def test_low_band_flags_pip(self):
		self.assertIn("needs improvement", PIP_RATING_BANDS)
		doc = SimpleNamespace(
			meta=SimpleNamespace(has_field=lambda _name: True),
			custom_qd_calibrated_score=None,
			final_score=1.8,
			custom_qd_rating_band=None,
			custom_qd_pip_required=0,
		)
		doc.get = lambda name, default=None: getattr(doc, name, default)
		with patch("qd_hrms.performance._appraisal_rating_scale", return_value="QD 5-Point Scale"):
			with patch("qd_hrms.performance._scale_levels", return_value=DEFAULT_LEVELS):
				apply_rating_band(doc)
		self.assertEqual(doc.custom_qd_rating_band, "Needs Improvement")
		self.assertEqual(doc.custom_qd_pip_required, 1)

	def test_parse_reviewers_from_dialog_rows(self):
		self.assertEqual(
			_parse_reviewers([{"employee": "HR-EMP-001"}, {"employee": "HR-EMP-002"}, {"employee": "HR-EMP-001"}]),
			["HR-EMP-001", "HR-EMP-002"],
		)

	def test_self_feedback_is_rejected(self):
		doc = SimpleNamespace(employee="HR-EMP-001", reviewer="HR-EMP-001", meta=SimpleNamespace(has_field=lambda _n: False))
		with self.assertRaises(frappe.ValidationError):
			validate_performance_feedback(doc)
