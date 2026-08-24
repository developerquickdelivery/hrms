"""Automated license and certification renewal tracking."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, now_datetime, today

from qd_hrms.self_service import get_session_employee, is_privileged

OPEN_LICENSE_STATUSES = ("Active", "Due for Renewal", "Renewal In Progress", "Expired")
CLOSED_REQUEST_STATES = ("Completed", "Rejected", "Withdrawn")
REQUEST_TYPE = "License Renewal"


def license_status(days_to_expiry, lead_days=0, current=None, has_open_renewal=False):
	"""Derive renewal status from remaining days and an open renewal request."""
	if current in ("Revoked", "Renewed"):
		return current
	days = int(days_to_expiry if days_to_expiry is not None else 0)
	lead = int(lead_days or 0)
	if days < 0:
		return "Expired"
	if has_open_renewal:
		return "Renewal In Progress"
	if lead and days <= lead:
		return "Due for Renewal"
	return "Active"


def has_open_renewal_request(request_name):
	if not request_name or not frappe.db.exists("QD Employee Request", request_name):
		return False
	state = frappe.db.get_value("QD Employee Request", request_name, "workflow_state")
	return state not in CLOSED_REQUEST_STATES


def license_query(user):
	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	return f"`tabQD Employee License`.employee = {frappe.db.escape(employee)}"


def has_license_permission(doc, ptype=None, user=None, debug=False):
	if is_privileged(user):
		return None
	employee = get_session_employee(user)
	if not employee or doc.get("employee") != employee:
		return False
	if ptype in ("write", "create", "delete", "submit", "cancel", "amend"):
		return False
	return True


def process_license_renewals():
	"""Daily: refresh status, open renewal requests, and mark overdue licenses."""
	if not frappe.db.exists("DocType", "QD Employee License"):
		return
	for name in frappe.get_all(
		"QD Employee License",
		filters={"status": ["not in", ["Renewed", "Revoked"]]},
		pluck="name",
	):
		try:
			_process_license(name)
		except Exception:
			frappe.log_error(
				title=f"License renewal failed: {name}",
				message=frappe.get_traceback(),
			)


def _process_license(name):
	doc = frappe.get_doc("QD Employee License", name)
	open_request = has_open_renewal_request(doc.renewal_request)
	if doc.renewal_request and not open_request:
		doc.renewal_request = None
	previous = doc.status
	doc.days_to_expiry = date_diff(doc.expiry_date, today())
	doc.status = license_status(
		doc.days_to_expiry,
		doc.renewal_lead_days,
		current=None,
		has_open_renewal=open_request,
	)
	if (
		doc.auto_renew
		and doc.status in ("Due for Renewal", "Expired")
		and not open_request
	):
		request_name = _open_renewal_request(doc)
		if request_name:
			doc.renewal_request = request_name
			doc.status = "Renewal In Progress" if doc.days_to_expiry >= 0 else "Expired"
			doc.last_alert_on = now_datetime()
	if previous != doc.status or doc.has_value_changed("renewal_request"):
		doc.save(ignore_permissions=True)
	else:
		frappe.db.set_value(
			"QD Employee License",
			doc.name,
			{
				"days_to_expiry": doc.days_to_expiry,
				"status": doc.status,
			},
			update_modified=False,
		)


def _open_renewal_request(doc):
	if not frappe.db.exists("DocType", "QD Employee Request"):
		return None
	_ensure_request_type()
	existing = frappe.db.exists(
		"QD Employee Request",
		{
			"request_type": REQUEST_TYPE,
			"employee": doc.employee,
			"reference_doctype": "QD Employee License",
			"reference_name": doc.name,
			"workflow_state": ["not in", CLOSED_REQUEST_STATES],
			"docstatus": ["<", 2],
		},
	)
	if existing:
		return existing
	priority = "Urgent" if date_diff(doc.expiry_date, today()) < 0 else "High"
	request = frappe.get_doc(
		{
			"doctype": "QD Employee Request",
			"employee": doc.employee,
			"request_type": REQUEST_TYPE,
			"request_date": today(),
			"priority": priority,
			"subject": _("Renew {0} for {1}").format(doc.license_type, doc.employee_name or doc.employee),
			"details": _(
				"Auto-opened renewal for {0}. Current license {1} expires on {2}. "
				"Attach the renewed certificate and submit for HR processing."
			).format(doc.license_type, doc.name, doc.expiry_date),
			"reference_doctype": "QD Employee License",
			"reference_name": doc.name,
			"requested_by": doc.employee_user or frappe.session.user,
		}
	)
	request.insert(ignore_permissions=True)
	return request.name


def _ensure_request_type():
	if frappe.db.exists("QD Employee Request Type", REQUEST_TYPE):
		return
	frappe.get_doc(
		{
			"doctype": "QD Employee Request Type",
			"request_type": REQUEST_TYPE,
			"description": "Renew an expiring employee license, permit, or certification.",
			"instructions": "Attach the renewed license or certificate and submit for HR processing.",
			"requires_attachment": 1,
			"requires_approval": 0,
			"default_priority": "High",
			"sla_days": 7,
			"suggested_reference_doctype": "QD Employee License",
		}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def record_license_renewal(license, issue_date, expiry_date, license_number=None, attachment=None):
	if not set(frappe.get_roles()) & {"System Manager", "HR Manager", "HR User"}:
		frappe.throw(_("Not permitted to record a license renewal."), frappe.PermissionError)
	source = frappe.get_doc("QD Employee License", license)
	source.check_permission("write")
	if source.status in ("Renewed", "Revoked"):
		frappe.throw(_("This license is already {0}.").format(source.status))
	if getdate(expiry_date) < getdate(issue_date):
		frappe.throw(_("Expiry Date cannot be before Issue Date."))
	renewed = frappe.get_doc(
		{
			"doctype": "QD Employee License",
			"employee": source.employee,
			"license_type": source.license_type,
			"license_number": license_number or source.license_number,
			"issuing_authority": source.issuing_authority,
			"issue_date": issue_date,
			"expiry_date": expiry_date,
			"auto_renew": source.auto_renew,
			"renewal_lead_days": source.renewal_lead_days,
			"required_for_work": source.required_for_work,
			"attachment": attachment,
			"renewed_from": source.name,
			"notes": _("Renewed from {0}.").format(source.name),
		}
	).insert()
	source.status = "Renewed"
	source.renewed_to = renewed.name
	if source.renewal_request:
		frappe.db.set_value(
			"QD Employee Request",
			source.renewal_request,
			{
				"reference_doctype": "QD Employee License",
				"reference_name": renewed.name,
			},
			update_modified=False,
		)
	source.save()
	return renewed.name
