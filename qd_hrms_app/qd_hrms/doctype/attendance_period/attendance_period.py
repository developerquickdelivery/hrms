# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

REOPEN_ROLES = {"System Manager", "HR Manager"}


class AttendancePeriod(Document):
	def validate(self):
		if getdate(self.start_date) > getdate(self.end_date):
			frappe.throw(_("Start Date cannot be after End Date."))
		self._assert_no_locked_overlap()

	def before_submit(self):
		self.status = "Locked"
		self.locked_by = frappe.session.user
		self.locked_date = now_datetime()

	def before_cancel(self):
		if not (set(frappe.get_roles()) & REOPEN_ROLES) and frappe.session.user != "Administrator":
			frappe.throw(_("Only HR Manager or System Manager can reopen a locked period."))
		if not self.reopening_reason:
			frappe.throw(_("Reopening Reason is required. Use the Reopen Period action."))

	def on_cancel(self):
		# Keep the original lock audit intact; cancellation is the audited reopening event.
		frappe.db.set_value(
			self.doctype,
			self.name,
			{
				"status": "Reopened",
				"reopened_by": frappe.session.user,
				"reopened_date": now_datetime(),
			},
			update_modified=False,
		)

	def _assert_no_locked_overlap(self):
		name = self.name or "New Attendance Period"
		overlap = frappe.db.sql(
			"""
			select name from `tabAttendance Period`
			where company = %s
				and docstatus = 1
				and status = 'Locked'
				and name != %s
				and start_date <= %s
				and end_date >= %s
			limit 1
			""",
			(self.company, name, self.end_date, self.start_date),
		)
		if overlap:
			frappe.throw(
				_("Overlaps locked Attendance Period {0}.").format(overlap[0][0]),
				title=_("Period already locked"),
			)


@frappe.whitelist()
def reopen_period(name: str, reason: str):
	if not (set(frappe.get_roles()) & REOPEN_ROLES) and frappe.session.user != "Administrator":
		frappe.throw(_("Only HR Manager or System Manager can reopen a locked period."))
	if not (reason or "").strip():
		frappe.throw(_("Reopening Reason is required."))

	doc = frappe.get_doc("Attendance Period", name)
	if doc.docstatus != 1 or doc.status != "Locked":
		frappe.throw(_("Attendance Period {0} is not locked.").format(name))

	doc.db_set("reopening_reason", reason.strip(), update_modified=False)
	doc.reload()
	doc.cancel()
	return {"name": doc.name, "status": "Reopened"}
