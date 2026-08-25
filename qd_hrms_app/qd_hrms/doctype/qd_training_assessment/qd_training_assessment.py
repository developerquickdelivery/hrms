import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, today


class QDTrainingAssessment(Document):
	def before_insert(self):
		self.assessor = self.assessor or frappe.session.user
		self.assessment_date = self.assessment_date or today()

	def validate(self):
		if not 0 <= flt(self.score) <= 100:
			frappe.throw(_("Score must be between 0 and 100."))
		self.result = "Passed" if flt(self.score) >= flt(self.passing_score) else "Failed"

	def on_submit(self):
		frappe.db.set_value(
			"QD Training Enrollment",
			self.enrollment,
			{"assessment": self.name, "status": "Completed" if self.result == "Passed" else "Attended"},
		)
		course = frappe.get_doc("QD Training Course", self.course)
		if self.result == "Passed" and course.certification_required and not self.certification:
			certificate = frappe.get_doc(
				{
					"doctype": "QD Training Certification",
					"employee": self.employee,
					"course": self.course,
					"training_session": self.training_session,
					"enrollment": self.enrollment,
					"assessment": self.name,
					"issue_date": self.assessment_date,
					"expiry_date": add_days(self.assessment_date, course.certificate_validity_days),
				}
			).insert(ignore_permissions=True)
			self.db_set("certification", certificate.name)
			frappe.db.set_value("QD Training Enrollment", self.enrollment, "certification", certificate.name)
			from qd_hrms.learning import supersede_previous_certificates

			supersede_previous_certificates(certificate)
