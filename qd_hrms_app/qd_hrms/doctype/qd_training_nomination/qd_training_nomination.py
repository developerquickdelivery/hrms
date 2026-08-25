import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class QDTrainingNomination(Document):
	def before_insert(self):
		self.nominated_by = self.nominated_by or frappe.session.user
		self.nomination_date = self.nomination_date or today()

	def validate(self):
		if self.training_session:
			program = frappe.db.get_value("Training Event", self.training_session, "training_program")
			if self.training_program and program and self.training_program != program:
				frappe.throw(_("Training Session does not belong to the selected Program."))

	def on_update(self):
		if self.status == "Approved" and self.training_session and not self.enrollment:
			enrollment = frappe.get_doc(
				{
					"doctype": "QD Training Enrollment",
					"employee": self.employee,
					"nomination": self.name,
					"training_request": self.training_request,
					"course": self.course,
					"training_program": self.training_program,
					"training_session": self.training_session,
				}
			).insert(ignore_permissions=True)
			self.db_set("enrollment", enrollment.name)
			self.db_set("status", "Enrolled")
