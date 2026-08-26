import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, today


class QDRecognitionAward(Document):
	def before_insert(self):
		if not self.recognized_by:
			self.recognized_by = frappe.session.user
		if not self.recognition_date:
			self.recognition_date = today()

	def validate(self):
		if self.employee and self.recognized_by:
			reviewer_emp = frappe.db.get_value("Employee", {"user_id": self.recognized_by}, "name")
			if reviewer_emp and reviewer_emp == self.employee:
				frappe.throw(_("Employees cannot nominate themselves for recognition."))

	def before_submit(self):
		if self.approval_status != "Approved":
			frappe.throw(_("Recognition must be approved through the workflow before submission."))
		self.approved_by = frappe.session.user
		self.approved_on = now_datetime()

	def on_submit(self):
		if flt(self.monetary_value) > 0 and not self.employee_incentive:
			self._create_incentive()

	def _create_incentive(self):
		if not frappe.db.exists("DocType", "Employee Incentive"):
			return
		component = frappe.db.get_value(
			"Salary Component",
			{"type": "Earning", "disabled": 0},
			"name",
		)
		if not component:
			return
		incentive = frappe.get_doc(
			{
				"doctype": "Employee Incentive",
				"employee": self.employee,
				"company": self.company,
				"payroll_date": self.recognition_date,
				"salary_component": component,
				"incentive_amount": self.monetary_value,
			}
		)
		incentive.insert(ignore_permissions=True)
		self.db_set("employee_incentive", incentive.name)
