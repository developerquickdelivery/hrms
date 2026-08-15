import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now, nowdate


class QDAssetLossDamageCase(Document):
	def before_insert(self):
		if not self.incident_date:
			self.incident_date = nowdate()

	def validate(self):
		if self.incident_date and getdate(self.incident_date) > getdate(nowdate()):
			frappe.throw(_("Incident Date cannot be in the future."))
		if self.assignment:
			assignment = frappe.db.get_value(
				"QD Employee Asset Assignment",
				self.assignment,
				["docstatus", "assignment_date", "status"],
				as_dict=True,
			)
			if not assignment or assignment.docstatus != 1:
				frappe.throw(_("Asset Assignment must be submitted before reporting loss or damage."))
			if getdate(self.incident_date) < getdate(assignment.assignment_date):
				frappe.throw(_("Incident Date cannot be before Assignment Date."))
			if assignment.status in ("Returned", "Financially Recovered", "Cancelled"):
				frappe.throw(_("A loss or damage case cannot be opened for a closed assignment."))
		if self.employee_liability and self.estimated_loss:
			if self.employee_liability > self.estimated_loss:
				frappe.throw(_("Employee Liability cannot exceed Estimated Loss / Repair Cost."))
		if self.docstatus == 0 and self.case_status == "Draft":
			self.case_status = "Reported"

	def before_submit(self):
		if not self.decision:
			frappe.throw(_("Decision is required before submitting the loss / damage case."))
		self.case_status = "Approved"
		self.reviewed_by = frappe.session.user
		self.reviewed_on = now()

	def on_submit(self):
		status = "Lost" if self.case_type == "Loss" else "Damaged"
		frappe.db.set_value(
			"QD Employee Asset Assignment",
			self.assignment,
			{"status": status, "loss_damage_case": self.name},
			update_modified=False,
		)

	def before_cancel(self):
		if self.asset_recovery and frappe.db.get_value(
			"QD Asset Recovery", self.asset_recovery, "docstatus"
		) == 1:
			frappe.throw(
				_("Cancel Asset Recovery {0} before cancelling this case.").format(self.asset_recovery)
			)

	def on_cancel(self):
		self.db_set("case_status", "Cancelled", update_modified=False)
		frappe.db.set_value(
			"QD Employee Asset Assignment",
			self.assignment,
			{"status": "Assigned", "loss_damage_case": None},
			update_modified=False,
		)
