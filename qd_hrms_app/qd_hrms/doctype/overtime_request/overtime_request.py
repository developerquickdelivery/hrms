# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime


class OvertimeRequest(Document):
	def before_insert(self):
		if frappe.session.user != "Administrator" and not self.employee:
			self.employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")

	def validate(self):
		if getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("From Date cannot be after To Date."))
		if flt(self.requested_hours) <= 0:
			frappe.throw(_("Requested Hours must be greater than zero."))
		if flt(self.approved_hours) < 0:
			frappe.throw(_("Approved Hours cannot be negative."))
		if flt(self.approved_hours) > flt(self.requested_hours):
			frappe.throw(_("Approved Hours cannot exceed Requested Hours."))
		if self.attendance:
			attendance = frappe.db.get_value(
				"Attendance",
				self.attendance,
				["employee", "attendance_date", "company"],
				as_dict=True,
			)
			if not attendance or attendance.employee != self.employee:
				frappe.throw(_("Attendance must belong to the selected Employee."))
			if not getdate(self.from_date) <= getdate(attendance.attendance_date) <= getdate(self.to_date):
				frappe.throw(_("Attendance Date must fall within the overtime request period."))

	def before_submit(self):
		roles = set(frappe.get_roles())
		if (
			frappe.session.user != "Administrator"
			and not roles.intersection({"System Manager", "HR Manager", "HR User"})
			and self.approver != frappe.session.user
		):
			frappe.throw(
				_("Only the employee's configured approver or HR may approve this request."),
				frappe.PermissionError,
			)
		if flt(self.approved_hours) <= 0:
			frappe.throw(_("Approved Hours must be greater than zero before approval."))
		self.approved_by = frappe.session.user
		self.approved_on = now_datetime()

	def on_submit(self):
		self._sync_attendance_overtime()

	def on_cancel(self):
		self._sync_attendance_overtime()

	def _sync_attendance_overtime(self):
		if not self.attendance:
			return
		total = frappe.db.sql(
			"""
			select coalesce(sum(approved_hours), 0)
			from `tabOvertime Request`
			where attendance = %s and docstatus = 1
			""",
			self.attendance,
		)[0][0]
		attendance = frappe.get_doc("Attendance", self.attendance)
		attendance.custom_qd_overtime_hours = flt(total)
		attendance.save(ignore_permissions=True)
