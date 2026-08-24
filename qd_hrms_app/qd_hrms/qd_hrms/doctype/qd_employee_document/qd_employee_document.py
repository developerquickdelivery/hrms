# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document

from qd_hrms.self_service import get_session_employee, is_privileged


class QDEmployeeDocument(Document):
	def before_insert(self):
		if not is_privileged():
			employee = get_session_employee()
			if employee:
				self.employee = employee
			self.issued_by_hr = 0
		elif self.issued_by_hr is None:
			self.issued_by_hr = 1

	def validate(self):
		if is_privileged():
			return
		employee = get_session_employee()
		if not employee:
			frappe.throw(_("Your user is not linked to an Employee record."))
		if self.employee != employee:
			frappe.throw(_("You can only upload documents for your own Employee record."))
		if not self.is_new():
			issued = frappe.db.get_value("QD Employee Document", self.name, "issued_by_hr")
			if issued:
				frappe.throw(_("HR-issued documents cannot be edited by employees."))

	def on_trash(self):
		if is_privileged():
			return
		if self.issued_by_hr:
			frappe.throw(_("HR-issued documents cannot be deleted."))
