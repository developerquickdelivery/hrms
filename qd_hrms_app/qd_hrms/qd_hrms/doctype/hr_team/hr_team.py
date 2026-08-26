# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document


class HRTeam(Document):
	def validate(self):
		employees = [row.employee for row in self.members if row.employee]
		if len(employees) != len(set(employees)):
			frappe.throw(_("An employee can only appear once in Team Members."))

		if self.team_leader and self.team_leader not in employees:
			frappe.msgprint(
				_("Team Leader is not listed in Team Members."),
				indicator="orange",
				alert=True,
			)

