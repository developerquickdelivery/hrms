import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry


class LeaveAdjustmentRequest(Document):
	def validate(self):
		if getdate(self.effective_from) > getdate(self.effective_to):
			frappe.throw(_("Effective From cannot be after Effective To."))
		if flt(self.days) <= 0:
			frappe.throw(_("Days must be greater than zero."))
		if self.employee and self.leave_type and self.effective_from:
			self.current_balance = get_leave_balance_on(
				self.employee, self.leave_type, self.effective_from
			)
		self._append_status_audit()

	def before_submit(self):
		if self.approval_status != "Approved":
			frappe.throw(_("The adjustment must be approved through the workflow before submission."))
		roles = set(frappe.get_roles())
		if (
			frappe.session.user != "Administrator"
			and not roles.intersection({"System Manager", "HR Manager", "HR User"})
			and self.approver != frappe.session.user
		):
			frappe.throw(
				_("Only the employee's configured approver or HR may approve this adjustment."),
				frappe.PermissionError,
			)
		self.approved_by = frappe.session.user
		self.approved_on = now_datetime()
		self._append_audit("Approved", self.reason)

	def on_submit(self):
		self._post_ledger(True)

	def before_cancel(self):
		if self.approval_status != "Cancelled":
			self.approval_status = "Cancelled"
			self._append_audit("Cancelled", self.reason)

	def on_cancel(self):
		self._post_ledger(False)

	def _post_ledger(self, submit):
		is_lwp = frappe.db.get_value("Leave Type", self.leave_type, "is_lwp") or 0
		value = flt(self.days) * (1 if self.adjustment_type == "Credit" else -1)
		create_leave_ledger_entry(
			self,
			{
				"leaves": value,
				"from_date": self.effective_from,
				"to_date": self.effective_to,
				"is_lwp": is_lwp,
				"is_carry_forward": 0,
			},
			submit=submit,
		)

	def _append_status_audit(self):
		if self.is_new() and not self.audit_history:
			self._append_audit("Created", self.reason)
		elif self.has_value_changed("approval_status"):
			self._append_audit(self.approval_status, self.reason)

	def _append_audit(self, action, remarks=None):
		self.append(
			"audit_history",
			{
				"action": action,
				"user": frappe.session.user,
				"timestamp": now_datetime(),
				"remarks": remarks,
			},
		)
