# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class QDPolicyAcknowledgement(Document):
	def validate(self):
		self._fill_name()
		if self.docstatus == 1 or self.status == "Signed":
			self._require_signature()

	def before_submit(self):
		self._require_signature()
		self.status = "Signed"
		self.signed_on = now_datetime()
		self.signed_by = frappe.session.user
		self.ip_address = getattr(frappe.local, "request_ip", None)

	def on_cancel(self):
		self.status = "Void"

	def _fill_name(self):
		if self.employee and not self.employee_name:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		if self.job_applicant and not self.employee_name:
			self.employee_name = frappe.db.get_value("Job Applicant", self.job_applicant, "applicant_name")

	def _require_signature(self):
		if not self.acknowledged:
			frappe.throw(_("Tick the acknowledgement checkbox after reading the policy."))
		if not self.typed_full_name:
			frappe.throw(_("Type your full name to attest this acknowledgement."))
		requires = 1
		if self.policy:
			requires = frappe.db.get_value("QD Policy", self.policy, "requires_signature")
		if requires and not self.signature:
			frappe.throw(_("Draw your e-signature before submitting."))
