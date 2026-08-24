"""Seed native cycle formulas, rating-scale fields, and peer-feedback Energy Points."""

from __future__ import annotations

import frappe


def execute():
	from qd_hrms.setup.performance import (
		ensure_custom_fields,
		ensure_cycle_score_formula,
		ensure_energy_points_recognition,
	)

	ensure_custom_fields()
	ensure_energy_points_recognition()
	ensure_cycle_score_formula()
	frappe.clear_cache()
