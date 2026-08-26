# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from qd_hrms.reporting import assignment_status, sync_employee_reports_to


class EmployeeReportingAssignment(Document):
	def validate(self):
		self._validate_dates()
		self._validate_managers()
		self._validate_overlap()
		self.effective_manager = self.acting_manager or self.primary_manager
		self._validate_reporting_cycle()
		if self.docstatus == 0:
			self.status = "Draft"

	def on_submit(self):
		status = assignment_status(self.effective_from, self.effective_to)
		self.db_set("status", status)
		if status == "Current":
			sync_employee_reports_to(self.employee)

	def on_cancel(self):
		manager = self.acting_manager or self.primary_manager
		self.db_set("status", "Cancelled")
		sync_employee_reports_to(self.employee, clear_manager=manager)

	def _validate_dates(self):
		if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
			frappe.throw(_("Effective To cannot be before Effective From."))

	def _validate_managers(self):
		managers = [
			manager
			for manager in (self.primary_manager, self.secondary_manager, self.acting_manager)
			if manager
		]
		if self.employee in managers:
			frappe.throw(_("An employee cannot be their own manager."))
		if len(managers) != len(set(managers)):
			frappe.throw(_("Primary, Secondary, and Acting Manager must be different employees."))

	def _validate_overlap(self):
		overlap = frappe.db.sql(
			"""
			select name
			from `tabEmployee Reporting Assignment`
			where employee = %s
				and docstatus = 1
				and name != %s
				and (effective_to is null or effective_to >= %s)
				and (%s is null or effective_from <= %s)
			limit 1
			""",
			(
				self.employee,
				self.name or "",
				self.effective_from,
				self.effective_to,
				self.effective_to,
			),
		)
		if overlap:
			frappe.throw(
				_("Reporting dates overlap submitted assignment {0}.").format(overlap[0][0])
			)

	def _validate_reporting_cycle(self):
		manager = self.acting_manager or self.primary_manager
		visited = {self.employee}
		while manager:
			if manager in visited:
				frappe.throw(_("This assignment creates a circular Reports To structure."))
			visited.add(manager)
			manager = frappe.db.get_value("Employee", manager, "reports_to")

