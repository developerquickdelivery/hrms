import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class QDEmployeeAssetAssignment(Document):
	def before_insert(self):
		if not self.assignment_date:
			self.assignment_date = nowdate()

	def validate(self):
		if self.expected_return and getdate(self.expected_return) < getdate(self.assignment_date):
			frappe.throw(_("Expected Return cannot be before Assignment Date."))
		if self.actual_return and getdate(self.actual_return) < getdate(self.assignment_date):
			frappe.throw(_("Actual Return cannot be before Assignment Date."))
		if self.is_new() or self.docstatus == 0:
			self.status = "Draft"

	def before_submit(self):
		active = frappe.db.get_value(
			"QD Employee Asset Assignment",
			{
				"asset": self.asset,
				"docstatus": 1,
				"status": ("in", ("Assigned", "Overdue", "Lost", "Damaged")),
				"name": ("!=", self.name),
			},
			"name",
		)
		if active:
			frappe.throw(_("Asset {0} is already assigned under {1}.").format(self.asset, active))
		self.status = "Assigned"

	def on_submit(self):
		self._update_asset_custody(self.employee, self.location)

	def before_cancel(self):
		if self.loss_damage_case and frappe.db.get_value(
			"QD Asset Loss Damage Case", self.loss_damage_case, "docstatus"
		) == 1:
			frappe.throw(
				_("Cancel submitted Loss / Damage Case {0} before cancelling this assignment.").format(
					self.loss_damage_case
				)
			)
		if self.asset_recovery and frappe.db.get_value(
			"QD Asset Recovery", self.asset_recovery, "docstatus"
		) == 1:
			frappe.throw(
				_("Cancel submitted Asset Recovery {0} before cancelling this assignment.").format(
					self.asset_recovery
				)
			)

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)
		self._clear_asset_custody()

	def _update_asset_custody(self, employee, location=None):
		values = {"custodian": employee}
		if location:
			values["location"] = location
		frappe.db.set_value("Asset", self.asset, values, update_modified=False)

	def _clear_asset_custody(self, location=None):
		if frappe.db.get_value("Asset", self.asset, "custodian") != self.employee:
			return
		values = {"custodian": None}
		if location:
			values["location"] = location
		frappe.db.set_value("Asset", self.asset, values, update_modified=False)
