from unittest import TestCase

from qd_hrms.qd_hrms.doctype.qd_performance_calibration.qd_performance_calibration import (
	BOX_LABELS,
)


class TestNineBox(TestCase):
	def test_all_nine_placements_are_defined(self):
		levels = ("Low", "Moderate", "High")
		self.assertEqual(
			set(BOX_LABELS),
			{(performance, potential) for performance in levels for potential in levels},
		)

	def test_future_leader_is_high_high(self):
		self.assertEqual(BOX_LABELS[("High", "High")], "Future Leader")

	def test_potential_gem_is_low_performance_high_potential(self):
		self.assertEqual(BOX_LABELS[("Low", "High")], "Potential Gem")
