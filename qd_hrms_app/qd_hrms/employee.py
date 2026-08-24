"""Employee validations for acting assignments."""

from __future__ import annotations

import frappe
from frappe import _


def validate(doc, method=None):
	from qd_hrms.self_service import is_self_service_user, restrict_employee_updates

	restrict_employee_updates(doc)
	if is_self_service_user():
		return
	_apply_position(doc)
	_set_default_grade(doc)
	_validate_employment_dates(doc)
	_validate_acting(doc)


def _apply_position(doc):
	position_name = doc.get("custom_qd_position")
	if not position_name:
		return

	position = frappe.db.get_value(
		"QD Position",
		position_name,
		[
			"active",
			"company",
			"branch",
			"business_unit",
			"department",
			"team",
			"designation",
			"employee_grade",
			"work_location",
			"reports_to_position",
		],
		as_dict=True,
	)
	if not position:
		frappe.throw(_("Position {0} does not exist.").format(position_name))
	if doc.status == "Active" and not position.active:
		frappe.throw(_("Position {0} is inactive.").format(position_name))

	if doc.status == "Active":
		occupant = frappe.db.get_value(
			"Employee",
			{
				"custom_qd_position": position_name,
				"status": "Active",
				"name": ("!=", doc.name),
			},
			"name",
		)
		if occupant:
			frappe.throw(
				_("Position {0} is already occupied by Employee {1}.").format(
					position_name,
					occupant,
				)
			)

	for target, value in (
		("company", position.company),
		("branch", position.branch),
		("department", position.department),
		("designation", position.designation),
		("grade", position.employee_grade),
		("custom_qd_business_unit", position.business_unit),
		("custom_qd_team", position.team),
		("custom_qd_work_location", position.work_location),
	):
		if value and doc.meta.has_field(target):
			doc.set(target, value)

	if position.reports_to_position and not doc.reports_to:
		doc.reports_to = frappe.db.get_value(
			"Employee",
			{
				"custom_qd_position": position.reports_to_position,
				"status": "Active",
			},
			"name",
		)


def _validate_employment_dates(doc):
	probation_start = doc.get("custom_qd_probation_start")
	probation_end = doc.get("custom_qd_probation_end")
	if probation_start and probation_end and probation_end < probation_start:
		frappe.throw(_("Probation End cannot be before Probation Start."))

	contract_start = doc.get("custom_qd_contract_start")
	contract_end = doc.get("contract_end_date")
	if contract_start and contract_end and contract_end < contract_start:
		frappe.throw(_("Contract End cannot be before Contract Start."))


def _set_default_grade(doc):
	"""Use Designation only as an optional default; Employee Grade stays independent."""
	if doc.get("grade") or not doc.get("designation"):
		return
	if not frappe.get_meta("Designation").has_field("custom_qd_default_employee_grade"):
		return
	grade = frappe.db.get_value(
		"Designation",
		doc.designation,
		"custom_qd_default_employee_grade",
	)
	if grade:
		doc.grade = grade


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
