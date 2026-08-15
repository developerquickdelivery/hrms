import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class QDPerformanceImprovementPlan(Document):
	def validate(self):
		if getdate(self.start_date) > getdate(self.end_date):
			frappe.throw(_("Start Date cannot be after End Date."))
		if not self.objectives:
			frappe.throw(_("Add at least one PIP objective."))

	def before_submit(self):
		if self.approval_status not in ("Active", "Successful", "Extended", "Unsuccessful"):
			frappe.throw(_("Activate or close the PIP through the workflow before submission."))
		if self.approval_status == "Active" and not self.acknowledged_on:
			self.acknowledged_on = now_datetime()

	def on_update_after_submit(self):
		if self.final_outcome and not self.closed_on:
			self.db_set("closed_on", now_datetime())
			if self.final_outcome != self.approval_status:
				self.db_set("approval_status", self.final_outcome)
