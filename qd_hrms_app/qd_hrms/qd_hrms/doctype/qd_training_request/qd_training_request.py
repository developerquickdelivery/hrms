import frappe
from frappe import _
from frappe.model.document import Document


class QDTrainingRequest(Document):
	def before_insert(self):
		if not self.employee:
			self.employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")

	def validate(self):
		manager = frappe.db.get_value("Employee", self.employee, "reports_to")
		self.manager_approver = (
			frappe.db.get_value("Employee", manager, "user_id") if manager else None
		)

	def on_submit(self):
		if self.approval_status != "Approved":
			frappe.throw(_("Training Request must be approved through the workflow."))
		if not self.nomination:
			nomination = frappe.get_doc(
				{
					"doctype": "QD Training Nomination",
					"employee": self.employee,
					"training_request": self.name,
					"course": self.course,
					"training_program": self.training_program,
					"nominated_by": frappe.session.user,
					"status": "Approved",
				}
			).insert(ignore_permissions=True)
			self.db_set("nomination", nomination.name)
