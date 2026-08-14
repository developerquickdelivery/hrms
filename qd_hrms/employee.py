"""Employee validations for acting assignments."""

from __future__ import annotations

import frappe
from frappe import _


def validate(doc, method=None):
	_validate_acting(doc)


def _validate_acting(doc):
	if not doc.get("custom_qd_is_acting"):
		return

	if not doc.get("custom_qd_acting_designation"):
		frappe.throw(_("Acting Designation is required when Currently Acting is checked."))

	if not doc.get("custom_qd_acting_from"):
		frappe.throw(_("Acting From date is required when Currently Acting is checked."))

	acting_to = doc.get("custom_qd_acting_to")
	if acting_to and doc.custom_qd_acting_from and acting_to < doc.custom_qd_acting_from:
		frappe.throw(_("Acting To cannot be before Acting From."))

	if doc.get("custom_qd_acting_for") and doc.custom_qd_acting_for == doc.name:
		frappe.throw(_("Acting For cannot be the same employee."))

	if doc.get("custom_qd_acting_designation") and frappe.db.exists("Designation", doc.custom_qd_acting_designation):
		eligible = frappe.db.get_value(
			"Designation", doc.custom_qd_acting_designation, "custom_qd_eligible_for_acting"
		)
		if eligible is not None and not eligible:
			frappe.msgprint(
				_("Designation {0} is not marked Eligible for Acting Assignment.").format(
					doc.custom_qd_acting_designation
				),
				indicator="orange",
				alert=True,
			)
