# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeEmploymentHistory(Document):
	def before_insert(self):
		if not self.flags.get("qd_system_generated"):
			frappe.throw(_("Employment History is created automatically and cannot be added manually."))

	def on_trash(self):
		frappe.throw(_("Employment History cannot be deleted."))
