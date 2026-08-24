"""Add Nine-Box calibration and move recognition to native Energy Points."""

from __future__ import annotations

import frappe


def execute():
	from qd_hrms.setup.performance import (
		ensure_custom_fields,
		ensure_energy_points_recognition,
		ensure_workspace,
		extend_ess,
	)
	from qd_hrms.setup.self_service import extend_ess_user_type

	ensure_custom_fields()
	frappe.db.sql(
		"""
		UPDATE `tabQD Performance Calibration`
		SET low_score_max = 2.49, high_score_min = 3.75
		WHERE COALESCE(low_score_max, 0) = 0 OR COALESCE(high_score_min, 0) = 0
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabQD Performance Calibration Row`
		SET potential_score = 3
		WHERE COALESCE(potential_score, 0) = 0
		"""
	)
	ensure_energy_points_recognition()
	ensure_workspace()
	extend_ess()
	extend_ess_user_type()
	frappe.clear_cache()
