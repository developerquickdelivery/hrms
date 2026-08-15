import frappe
from frappe.model.document import Document
from frappe.utils import now


class QDHRIntegrationAudit(Document):
	def before_insert(self):
		self.event_time = self.event_time or now()
		self.performed_by = self.performed_by or frappe.session.user or "Administrator"

	def before_save(self):
		if not self.is_new():
			frappe.throw("Integration audit records are immutable.")
