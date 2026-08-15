# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document


class HRBusinessUnit(Document):
	def validate(self):
		if self.parent_unit == self.name:
			frappe.throw(_("A Business Unit cannot be its own Parent Unit."))
		self._validate_parent_cycle()

	def _validate_parent_cycle(self):
		parent = self.parent_unit
		visited = {self.name}
		while parent:
			if parent in visited:
				frappe.throw(_("Parent Unit creates a circular Business Unit hierarchy."))
			visited.add(parent)
			parent = frappe.db.get_value("HR Business Unit", parent, "parent_unit")

