import frappe
from frappe.model.document import Document
from frappe.utils import today


class QDTrainingEnrollment(Document):
	def before_insert(self):
		self.enrollment_date = self.enrollment_date or today()

	def validate(self):
		if self.employee and self.training_session:
			duplicate = frappe.db.exists(
				"QD Training Enrollment",
				{
					"employee": self.employee,
					"training_session": self.training_session,
					"name": ("!=", self.name or ""),
					"status": ("not in", ("Withdrawn", "Cancelled")),
				},
			)
			if duplicate:
				frappe.throw("Employee is already enrolled in this Training Session.")
