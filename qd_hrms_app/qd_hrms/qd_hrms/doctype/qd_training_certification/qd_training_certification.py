import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, today


class QDTrainingCertification(Document):
	def after_insert(self):
		if not self.certificate_number:
			self.db_set("certificate_number", self.name)

	def validate(self):
		if getdate(self.expiry_date) < getdate(self.issue_date):
			frappe.throw(_("Expiry Date cannot be before Issue Date."))
		self.days_to_expiry = date_diff(self.expiry_date, today())
		if self.status not in ("Revoked", "Renewed"):
			self.status = "Expired" if self.days_to_expiry < 0 else "Active"
