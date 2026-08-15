import frappe
from frappe import _
from frappe.model.document import Document


class QDEmployeeRequestType(Document):
	def validate(self):
		if self.sla_days < 0:
			frappe.throw(_("SLA Days cannot be negative."))
		if self.requires_approval and self.approval_route == "Specific User":
			if not self.specific_approver:
				frappe.throw(_("Specific Approver is required for the selected approval route."))
		if not self.requires_approval:
			self.approval_route = None
			self.specific_approver = None
