"""Post-migrate patch for idempotent desk metadata."""

from __future__ import annotations

import frappe


def execute():
	from qd_hrms.setup.install import after_migrate

	after_migrate()
	frappe.db.commit()
