"""Install license / certification auto-renewal tracking."""

from __future__ import annotations

import frappe


def execute():
	from qd_hrms.setup.licenses import run

	run()
	frappe.clear_cache()
