import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class QDAssetRecovery(Document):
	def before_insert(self):
		if not self.recovery_date:
			self.recovery_date = nowdate()

	def validate(self):
		assignment = frappe.db.get_value(
			"QD Employee Asset Assignment",
			self.assignment,
			["docstatus", "assignment_date", "status", "loss_damage_case"],
			as_dict=True,
		)
		if not assignment or assignment.docstatus != 1:
			frappe.throw(_("Asset Assignment must be submitted before recording recovery."))
		if assignment.status in ("Returned", "Financially Recovered", "Cancelled"):
			frappe.throw(_("This asset assignment is already closed."))
		if getdate(self.recovery_date) < getdate(assignment.assignment_date):
			frappe.throw(_("Recovery Date cannot be before Assignment Date."))
		if self.loss_damage_case:
			case_assignment = frappe.db.get_value(
				"QD Asset Loss Damage Case", self.loss_damage_case, "assignment"
			)
			if case_assignment != self.assignment:
				frappe.throw(_("Loss / Damage Case must belong to the selected assignment."))
		elif assignment.loss_damage_case:
			self.loss_damage_case = assignment.loss_damage_case

	def before_submit(self):
		duplicate = frappe.db.get_value(
			"QD Asset Recovery",
			{"assignment": self.assignment, "docstatus": 1, "name": ("!=", self.name)},
			"name",
		)
		if duplicate:
			frappe.throw(_("Assignment already has submitted recovery {0}.").format(duplicate))
		self.recovery_status = "Completed"

	def on_submit(self):
		physical = self.recovery_type in ("Physical Return", "Replacement")
		values = {
			"actual_return": self.recovery_date,
			"asset_recovery": self.name,
			"status": "Returned" if physical else "Financially Recovered",
		}
		if physical:
			values.update(
				{
					"return_condition": self.asset_condition,
					"returned_location": self.returned_location,
				}
			)
		frappe.db.set_value(
			"QD Employee Asset Assignment", self.assignment, values, update_modified=False
		)
		if self.loss_damage_case:
			frappe.db.set_value(
				"QD Asset Loss Damage Case",
				self.loss_damage_case,
				{"asset_recovery": self.name, "case_status": "Resolved"},
				update_modified=False,
			)
		assignment = frappe.get_doc("QD Employee Asset Assignment", self.assignment)
		assignment._clear_asset_custody(self.returned_location if physical else None)

	def on_cancel(self):
		self.db_set("recovery_status", "Cancelled", update_modified=False)
		previous_status = "Assigned"
		if self.loss_damage_case:
			case_type = frappe.db.get_value(
				"QD Asset Loss Damage Case", self.loss_damage_case, "case_type"
			)
			previous_status = "Lost" if case_type == "Loss" else "Damaged"
			frappe.db.set_value(
				"QD Asset Loss Damage Case",
				self.loss_damage_case,
				{"asset_recovery": None, "case_status": "Approved"},
				update_modified=False,
			)
		frappe.db.set_value(
			"QD Employee Asset Assignment",
			self.assignment,
			{
				"actual_return": None,
				"return_condition": None,
				"returned_location": None,
				"asset_recovery": None,
				"status": previous_status,
			},
			update_modified=False,
		)
		assignment = frappe.get_doc("QD Employee Asset Assignment", self.assignment)
		assignment._update_asset_custody(assignment.employee, assignment.location)
