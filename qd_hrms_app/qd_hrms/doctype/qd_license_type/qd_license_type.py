import frappe
from frappe import _
from frappe.model.document import Document


class QDLicenseType(Document):
	def validate(self):
		if (self.default_validity_days or 0) <= 0:
			frappe.throw(_("Default Validity must be greater than zero."))
		if (self.renewal_lead_days or 0) < 0:
			frappe.throw(_("Renewal Lead Time cannot be negative."))
		if self.renewal_lead_days and self.default_validity_days and self.renewal_lead_days >= self.default_validity_days:
			frappe.throw(_("Renewal Lead Time must be shorter than Default Validity."))
