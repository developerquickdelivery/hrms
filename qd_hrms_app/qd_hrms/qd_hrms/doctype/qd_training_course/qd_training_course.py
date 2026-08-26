import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class QDTrainingCourse(Document):
	def validate(self):
		if self.assessment_required and not 0 <= flt(self.passing_score) <= 100:
			frappe.throw(_("Passing Score must be between 0 and 100."))
		if self.certification_required and (self.certificate_validity_days or 0) <= 0:
			frappe.throw(_("Certificate Validity must be greater than zero."))
