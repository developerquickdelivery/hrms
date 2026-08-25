import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, today

from qd_hrms.licenses import has_open_renewal_request, license_status
from qd_hrms.self_service import get_session_employee, is_privileged

OPEN_STATUSES = ("Active", "Due for Renewal", "Renewal In Progress", "Expired")


class QDEmployeeLicense(Document):
	def validate(self):
		if not is_privileged() and self.employee != get_session_employee():
			frappe.throw(_("You can only view your own licenses."))
		if getdate(self.expiry_date) < getdate(self.issue_date):
			frappe.throw(_("Expiry Date cannot be before Issue Date."))
		self._apply_type_defaults()
		self.days_to_expiry = date_diff(self.expiry_date, today())
		self.renewal_window_start = add_days(self.expiry_date, -(self.renewal_lead_days or 0))
		if self.status not in ("Revoked", "Renewed"):
			self.status = license_status(
				self.days_to_expiry,
				self.renewal_lead_days,
				current=self.status,
				has_open_renewal=has_open_renewal_request(self.renewal_request),
			)
		if self.status == "Revoked" and not self.revocation_reason:
			frappe.throw(_("Revocation Reason is required."))
		self._assert_single_open_license()

	def _apply_type_defaults(self):
		if not self.license_type:
			return
		license_type = frappe.db.get_value(
			"QD License Type",
			self.license_type,
			[
				"is_active",
				"auto_renew_default",
				"renewal_lead_days",
				"required_for_work",
				"issuing_authority",
			],
			as_dict=True,
		)
		if not license_type:
			return
		if not license_type.is_active and self.is_new():
			frappe.throw(_("License type {0} is not active.").format(self.license_type))
		if self.renewal_lead_days in (None, ""):
			self.renewal_lead_days = license_type.renewal_lead_days
		if self.is_new():
			if self.auto_renew in (None, ""):
				self.auto_renew = license_type.auto_renew_default
			if not self.required_for_work:
				self.required_for_work = license_type.required_for_work
			if not self.issuing_authority:
				self.issuing_authority = license_type.issuing_authority

	def _assert_single_open_license(self):
		if self.status not in OPEN_STATUSES:
			return
		filters = {
			"employee": self.employee,
			"license_type": self.license_type,
			"status": ["in", OPEN_STATUSES],
			"name": ["!=", self.name or ""],
		}
		existing = frappe.db.exists("QD Employee License", filters)
		if existing and existing != self.renewed_from:
			frappe.throw(
				_("Employee {0} already has an open {1} license ({2}).").format(
					self.employee_name or self.employee, self.license_type, existing
				)
			)
