"""Attendance Request override used as Quick Delivery Attendance Correction."""

import frappe
from frappe import _
from frappe.utils import formatdate
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest

PRIVILEGED_APPROVER_ROLES = {"System Manager", "HR Manager", "HR User"}


class QDAttendanceRequest(AttendanceRequest):
	def validate(self):
		super().validate()
		if not self.custom_qd_requested_status:
			frappe.throw(_("Requested Attendance Status is required."))
		self._set_original_attendance_summary()

	def before_submit(self):
		self._validate_approver()

	def get_attendance_status(self, attendance_date):
		if self.get("custom_qd_requested_status"):
			return self.custom_qd_requested_status
		return super().get_attendance_status(attendance_date)

	def _validate_approver(self):
		roles = set(frappe.get_roles())
		if roles & PRIVILEGED_APPROVER_ROLES or frappe.session.user == "Administrator":
			return
		approver = frappe.db.get_value("Employee", self.employee, "leave_approver")
		if not approver or approver != frappe.session.user:
			frappe.throw(
				_("Only the employee's configured Leave Approver or HR may approve this correction."),
				frappe.PermissionError,
			)

	def _set_original_attendance_summary(self):
		rows = frappe.get_all(
			"Attendance",
			filters={
				"employee": self.employee,
				"attendance_date": ["between", [self.from_date, self.to_date]],
				"docstatus": 1,
			},
			fields=["attendance_date", "status"],
			order_by="attendance_date",
		)
		if not rows:
			self.custom_qd_original_status = _("No submitted Attendance")
			return
		self.custom_qd_original_status = "; ".join(
			f"{formatdate(row.attendance_date)}: {row.status}" for row in rows
		)
