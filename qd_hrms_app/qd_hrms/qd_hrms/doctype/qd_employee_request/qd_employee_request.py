import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, now, nowdate

from qd_hrms.self_service import get_session_employee, is_self_service_user


class QDEmployeeRequest(Document):
	def before_insert(self):
		if not self.employee and is_self_service_user():
			self.employee = get_session_employee()
		if not self.requested_by:
			self.requested_by = frappe.session.user
		if not self.request_date:
			self.request_date = nowdate()
		self._apply_type_configuration()

	def validate(self):
		if (
			is_self_service_user()
			and self.employee != get_session_employee()
			and self.approver != frappe.session.user
		):
			frappe.throw(_("You can only update your own requests or requests assigned to you for approval."))
		if self.request_date and getdate(self.request_date) > getdate(nowdate()):
			frappe.throw(_("Request Date cannot be in the future."))
		if self.is_new() or self.has_value_changed("request_type"):
			self._apply_type_configuration()
		if self.request_type == "Custom Request" and not self.custom_request_type:
			frappe.throw(_("Custom Request Type is required."))
		if self.workflow_state != "Draft" and self.requires_attachment and not self.attachment:
			frappe.throw(
				_("A supporting attachment is required for request type {0}.").format(
					self.request_type
				)
			)
		self._validate_stage_transition()

	def before_submit(self):
		if self.workflow_state != "Completed":
			frappe.throw(_("Only completed employee requests can be submitted."))
		if not self.completion_summary:
			frappe.throw(_("Completion Summary is required before completing the request."))

	def _apply_type_configuration(self):
		if not self.request_type:
			return
		config = frappe.db.get_value(
			"QD Employee Request Type",
			self.request_type,
			[
				"is_active",
				"requires_attachment",
				"requires_approval",
				"approval_route",
				"specific_approver",
				"default_priority",
				"sla_days",
			],
			as_dict=True,
		)
		if not config or not config.is_active:
			frappe.throw(_("Request type {0} is not active.").format(self.request_type))
		self.requires_attachment = config.requires_attachment
		self.requires_approval = config.requires_approval
		self.approval_route = config.approval_route
		if self.is_new() or self.has_value_changed("request_type"):
			self.priority = config.default_priority
			self.due_date = add_days(self.request_date or nowdate(), config.sla_days or 0)
		self.approver = self._resolve_approver(config)
		self.approval_status = "Pending" if config.requires_approval else "Not Required"

	def _resolve_approver(self, config):
		if not config.requires_approval or config.approval_route == "HR Manager":
			return None
		if config.approval_route == "Specific User":
			return config.specific_approver
		manager = frappe.db.get_value("Employee", self.employee, "reports_to")
		approver = manager and frappe.db.get_value("Employee", manager, "user_id")
		if not approver:
			frappe.throw(
				_("Reporting Manager must have a linked User before this request can be routed.")
			)
		if approver == self.requested_by:
			frappe.throw(_("Employees cannot approve their own requests."))
		return approver

	def _validate_stage_transition(self):
		if not self.has_value_changed("workflow_state"):
			return
		previous = self.get_doc_before_save()
		previous_state = previous.workflow_state if previous else None

		if self.workflow_state in ("Pending Approval", "HR Processing"):
			if previous_state == "Pending Validation":
				if self.validation_status == "Invalid":
					frappe.throw(_("An invalid request cannot proceed."))
				self.validation_status = "Valid"
				self.validated_by = frappe.session.user
				self.validated_on = now()

		if self.workflow_state == "Pending Approval" and not self.requires_approval:
			frappe.throw(_("This request type does not require approval. Route it to HR Processing."))

		if self.workflow_state == "HR Processing":
			if previous_state == "Pending Approval":
				self.approval_status = "Approved"
				self.approved_by = frappe.session.user
				self.approved_on = now()
			elif not self.requires_approval:
				self.approval_status = "Not Required"
			if not self.assigned_to:
				self.assigned_to = frappe.session.user

		if self.workflow_state == "Rejected":
			if not self.rejection_reason:
				frappe.throw(_("Rejection Reason is required."))
			self.approval_status = "Rejected"

		if self.workflow_state == "Completed":
			if previous_state != "HR Processing":
				frappe.throw(_("The request must be in HR Processing before completion."))
			if not self.completion_summary:
				frappe.throw(_("Completion Summary is required."))
			self.completed_by = frappe.session.user
			self.completed_on = now()
