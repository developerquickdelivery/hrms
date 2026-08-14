# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class QDAttendancePeriodLock(Document):
	def validate(self):
		if getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("From Date cannot be after To Date."))
		self._assert_no_overlap()

	def before_submit(self):
		self.locked_by = frappe.session.user
		self.locked_on = now_datetime()

	def on_cancel(self):
		self.db_set("locked_by", None)
		self.db_set("locked_on", None)

	def _assert_no_overlap(self):
		name = self.name or "New QD Attendance Period Lock"
		overlap = frappe.db.sql(
			"""
			select name from `tabQD Attendance Period Lock`
			where company = %s
				and docstatus = 1
				and name != %s
				and from_date <= %s
				and to_date >= %s
			limit 1
			""",
			(self.company, name, self.to_date, self.from_date),
		)
		if overlap:
			frappe.throw(
				_("Overlaps submitted period lock {0}.").format(overlap[0][0]),
				title=_("Period already locked"),
			)
