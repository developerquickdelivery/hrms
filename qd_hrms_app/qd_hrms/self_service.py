"""Own-record access helpers for Employee Self Service."""

from __future__ import annotations

import frappe
from frappe import _

PRIVILEGED_ROLES = (
	"System Manager",
	"HR Manager",
	"HR User",
	"Payroll Manager",
)

CONTACT_FIELDS = frozenset(
	{
		"image",
		"cell_number",
		"personal_email",
		"prefered_contact_email",
		"prefered_email",
		"current_address",
		"current_accommodation_type",
		"permanent_address",
		"permanent_accommodation_type",
		"person_to_be_contacted",
		"emergency_phone_number",
		"relation",
		"bio",
		"unsubscribed",
	}
)

BREAK_FIELDTYPES = frozenset(
	{
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
		"Button",
		"Heading",
		"Fold",
	}
)


def get_session_employee(user=None):
	user = user or frappe.session.user
	cache = getattr(frappe.local, "qd_employee_by_user", None)
	if cache is None:
		cache = {}
		frappe.local.qd_employee_by_user = cache
	if user not in cache:
		cache[user] = frappe.db.get_value("Employee", {"user_id": user}, "name")
	return cache[user]


def is_privileged(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & set(PRIVILEGED_ROLES))


def is_self_service_user(user=None):
	user = user or frappe.session.user
	if user in ("Administrator", "Guest") or is_privileged(user):
		return False
	roles = frappe.get_roles(user)
	return "Employee Self Service" in roles or "Employee" in roles


def extend_bootinfo(bootinfo):
	if not frappe.session.user or frappe.session.user == "Guest":
		return
	bootinfo.employee = get_session_employee()
	bootinfo.qd_is_self_service = is_self_service_user()


def restrict_employee_updates(doc):
	if not is_self_service_user():
		return
	if doc.is_new():
		frappe.throw(_("You cannot create Employee records."))
	employee = get_session_employee()
	if not employee or doc.name != employee:
		frappe.throw(_("You can only update your own Employee profile."))
	changed = []
	for field in doc.meta.fields:
		if (
			field.fieldtype in BREAK_FIELDTYPES
			or field.fieldname in CONTACT_FIELDS
			or field.read_only
			or field.fetch_from
		):
			continue
		if doc.has_value_changed(field.fieldname):
			changed.append(field.label or field.fieldname)
	if changed:
		frappe.throw(
			_("You can only update your contact details. Restricted fields: {0}").format(
				", ".join(changed[:8])
			)
		)


def asset_query(user):
	return _field_query("Asset", "custodian", user)


def training_event_query(user):
	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	escaped = frappe.db.escape(employee)
	return (
		"`tabTraining Event`.name IN ("
		"SELECT parent FROM `tabTraining Event Employee` "
		f"WHERE employee = {escaped})"
	)


def qd_employee_document_query(user):
	return _field_query("QD Employee Document", "employee", user)


def qd_policy_acknowledgement_query(user):
	return _field_query("QD Policy Acknowledgement", "employee", user)


def energy_point_log_query(user):
	if is_privileged(user):
		return ""
	return f"`tabEnergy Point Log`.user = {frappe.db.escape(user)}"


def has_energy_point_log_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	user = user or frappe.session.user
	return ptype == "read" and doc.get("user") == user


def has_asset_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	employee = get_session_employee(user)
	if not employee:
		return False
	return doc.get("custodian") == employee


def has_training_event_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	employee = get_session_employee(user)
	if not employee:
		return False
	return bool(
		frappe.db.exists(
			"Training Event Employee",
			{"parent": doc.name, "employee": employee},
		)
	)


def has_employee_document_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	employee = get_session_employee(user)
	if not employee or doc.get("employee") != employee:
		return False
	if ptype == "delete" and doc.get("issued_by_hr"):
		return False
	return True


def has_policy_acknowledgement_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	employee = get_session_employee(user)
	if not employee:
		return False
	return doc.get("employee") == employee


def _field_query(doctype, fieldname, user):
	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	return f"`tab{doctype}`.{fieldname} = {frappe.db.escape(employee)}"
