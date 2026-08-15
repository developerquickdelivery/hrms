import frappe
from frappe import _
from frappe.utils import getdate, today

from qd_hrms.attendance.period_lock import assert_period_open


def validate_leave_application(doc, method=None):
	if doc.company and doc.from_date:
		assert_period_open(
			doc.company,
			doc.from_date,
			_("create or change a Leave Application"),
			doc.to_date or doc.from_date,
		)


def before_submit_leave_application(doc, method=None):
	if doc.status != "Approved":
		return
	roles = set(frappe.get_roles())
	if frappe.session.user == "Administrator" or roles.intersection(
		{"System Manager", "HR Manager", "HR User"}
	):
		return
	if doc.leave_approver != frappe.session.user:
		frappe.throw(
			_("Only the configured Leave Approver or HR may approve this application."),
			frappe.PermissionError,
		)


def before_cancel_leave_application(doc, method=None):
	validate_leave_application(doc)
	roles = set(frappe.get_roles())
	if getdate(doc.from_date) <= getdate(today()) and not roles.intersection(
		{"System Manager", "HR Manager", "HR User"}
	):
		frappe.throw(
			_("Leave that has started can only be cancelled by HR."),
			frappe.PermissionError,
		)


def validate_leave_adjustment(doc, method=None):
	if doc.company and doc.effective_from:
		assert_period_open(
			doc.company,
			doc.effective_from,
			_("create or change a Leave Adjustment Request"),
			doc.effective_to or doc.effective_from,
		)


@frappe.whitelist()
def get_my_leave_balances(date=None):
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details
	from qd_hrms.self_service import get_session_employee

	employee = get_session_employee()
	if not employee:
		return {}
	return get_leave_details(employee, date or today()).get("leave_allocation", {})
