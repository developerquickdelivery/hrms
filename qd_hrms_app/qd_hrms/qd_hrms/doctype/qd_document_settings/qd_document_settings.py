import frappe
from frappe import _
from frappe.model.document import Document


class QDDocumentSettings(Document):
	def validate(self):
		if (
			self.expiry_final_reminder_days
			and self.expiry_first_reminder_days
			and self.expiry_final_reminder_days > self.expiry_first_reminder_days
		):
			frappe.throw(
				_("Final Expiry Reminder must be closer to expiry than the First Expiry Reminder.")
			)
