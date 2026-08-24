"""Automatic Employee Employment History recording."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import nowdate

# Field changes on Employee → history event type.
EMPLOYEE_FIELD_EVENTS = (
	("designation", "Promotion"),
	("branch", "Transfer"),
	("grade", "Grade Change"),
	("custom_qd_position", "Position Change"),
	("department", "Department Change"),
	("reports_to", "Manager Change"),
	("status", "Status Change"),
)


def on_employee_insert(doc, method=None):
	record_event(
		employee=doc.name,
		event_type="Hiring",
		from_value=None,
		to_value=doc.status,
		reference_doctype="Employee",
		reference_name=doc.name,
		remarks=_("Employee record created."),
	)


def on_employee_update(doc, method=None):
	if doc.flags.get("qd_skip_employment_history"):
		return

	before = doc.get_doc_before_save()
	for fieldname, event_type in EMPLOYEE_FIELD_EVENTS:
		if fieldname.startswith("custom_") and not doc.meta.has_field(fieldname):
			continue
		if not doc.has_value_changed(fieldname):
			continue
		record_event(
			employee=doc.name,
			event_type=event_type,
			from_value=before.get(fieldname) if before else None,
			to_value=doc.get(fieldname),
			reference_doctype="Employee",
			reference_name=doc.name,
		)


def on_salary_structure_assignment_submit(doc, method=None):
	previous = frappe.db.get_value(
		"Salary Structure Assignment",
		{
			"employee": doc.employee,
			"docstatus": 1,
			"name": ("!=", doc.name),
			"from_date": ("<=", doc.from_date),
		},
		["name", "base", "salary_structure"],
		order_by="from_date desc",
		as_dict=True,
	)
	from_value = None
	if previous:
		from_value = _format_salary(previous.salary_structure, previous.base)
	record_event(
		employee=doc.employee,
		event_type="Salary Change",
		from_value=from_value,
		to_value=_format_salary(doc.salary_structure, doc.base),
		reference_doctype="Salary Structure Assignment",
		reference_name=doc.name,
		event_date=doc.from_date,
		remarks=doc.get("custom_qd_salary_change_type") or None,
	)


def record_event(
	*,
	employee: str,
	event_type: str,
	from_value=None,
	to_value=None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	event_date=None,
	remarks: str | None = None,
):
	if not employee or not event_type:
		return
	if from_value == to_value and event_type != "Hiring":
		return
	if not frappe.db.exists("DocType", "Employee Employment History"):
		return

	employee_name = frappe.db.get_value("Employee", employee, "employee_name")
	doc = frappe.get_doc(
		{
			"doctype": "Employee Employment History",
			"naming_series": "QD-EEH-.YYYY.-",
			"employee": employee,
			"employee_name": employee_name,
			"event_type": event_type,
			"event_date": event_date or nowdate(),
			"from_value": _as_text(from_value),
			"to_value": _as_text(to_value),
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"changed_by": getattr(frappe.session, "user", None) or "Administrator",
			"remarks": remarks,
		}
	)
	doc.flags.qd_system_generated = True
	doc.flags.ignore_permissions = True
	doc.insert()


def _format_salary(structure, base) -> str:
	parts = []
	if structure:
		parts.append(str(structure))
	if base is not None:
		parts.append(f"Base {base}")
	return " / ".join(parts) if parts else ""


def _as_text(value) -> str | None:
	if value is None:
		return None
	return str(value)
