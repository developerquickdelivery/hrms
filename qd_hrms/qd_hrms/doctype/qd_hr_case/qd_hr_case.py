import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class QDHRCase(Document):
	def before_insert(self):
		if not self.raised_by:
			self.raised_by = frappe.session.user
		if not self.opened_on:
			self.opened_on = nowdate()
		if not self.case_manager:
			self.case_manager = frappe.session.user

	def validate(self):
		self.validate_dates()
		self.validate_investigation()
		self.validate_decision()
		self.validate_appeal()
		self.validate_closure()

	def validate_dates(self):
		if self.investigation_start and self.investigation_end and getdate(
			self.investigation_end
		) < getdate(self.investigation_start):
			frappe.throw(_("Investigation End cannot be before Investigation Start."))
		if self.decision_date and getdate(self.decision_date) < getdate(self.opened_on):
			frappe.throw(_("Decision Date cannot be before the case Opened On date."))
		if self.closure_date and getdate(self.closure_date) < getdate(self.opened_on):
			frappe.throw(_("Closure Date cannot be before the case Opened On date."))

	def validate_investigation(self):
		if self.investigation_status in ("In Progress", "Completed"):
			if not self.investigator:
				frappe.throw(_("Investigator is required when investigation is in progress or completed."))
			if not self.investigation_start:
				self.investigation_start = nowdate()
		if self.investigation_status == "Completed" and not self.investigation_findings:
			frappe.throw(_("Investigation Findings are required when investigation is completed."))

	def validate_decision(self):
		if self.case_status in ("Decision Issued", "Appealed", "Closed"):
			if not self.decision_type or not self.decision_summary:
				frappe.throw(
					_("Decision and Decision Summary are required before issuing a decision on case {0}.").format(
						self.name
					)
				)
			if not self.decision_date:
				self.decision_date = nowdate()
			if not self.decision_by:
				self.decision_by = frappe.session.user

	def validate_appeal(self):
		if self.case_status == "Appealed" and not self.appeal_filed:
			self.appeal_filed = 1
		if self.appeal_filed:
			if not self.appeal_date:
				self.appeal_date = nowdate()
			if not self.appeal_outcome:
				self.appeal_outcome = "Pending"

	def validate_closure(self):
		if self.case_status == "Closed":
			if not self.resolution:
				frappe.throw(_("Resolution is required to close the case."))
			if not self.closure_summary:
				frappe.throw(_("Closure Summary is required to close the case."))
			if self.appeal_filed and self.appeal_outcome in (None, "", "Pending"):
				frappe.throw(_("Appeal Outcome must be recorded before closing an appealed case."))
			if not self.closure_date:
				self.closure_date = nowdate()
			if not self.closed_by:
				self.closed_by = frappe.session.user

	def before_submit(self):
		if self.case_status != "Closed":
			frappe.throw(
				_("Only cases with status 'Closed' can be submitted. Use the workflow actions to progress the case.")
			)

	def on_submit(self):
		self._sync_source_status("Closed")

	def on_cancel(self):
		self._sync_source_status("Reopened")

	def on_update_after_submit(self):
		# allow appeal details / participants / evidence updates post-closure
		pass

	def _sync_source_status(self, status):
		if not (self.source_doctype and self.source_name):
			return
		if not frappe.db.exists(self.source_doctype, self.source_name):
			return
		if frappe.get_meta(self.source_doctype).has_field("case_outcome_status"):
			frappe.db.set_value(
				self.source_doctype, self.source_name, "case_outcome_status", status, update_modified=False
			)


@frappe.whitelist()
def make_hr_case(source_doctype, source_name):
	"""Create (or return existing) QD HR Case for an intake record."""
	if source_doctype not in ("QD Disciplinary Case", "QD Grievance", "QD Complaint"):
		frappe.throw(_("Unsupported source document type."))

	existing = frappe.db.get_value(
		"QD HR Case", {"source_doctype": source_doctype, "source_name": source_name}, "name"
	)
	if existing:
		return existing

	src = frappe.get_doc(source_doctype, source_name)
	case_type = {
		"QD Disciplinary Case": "Disciplinary Case",
		"QD Grievance": "Grievance",
		"QD Complaint": "Complaint",
	}[source_doctype]

	case = frappe.new_doc("QD HR Case")
	case.case_type = case_type
	case.employee = src.employee
	case.subject = src.subject
	case.details = src.get("details") or src.get("description") or src.subject
	case.raised_by = src.owner
	case.opened_on = nowdate()
	case.source_doctype = source_doctype
	case.source_name = source_name
	case.insert(ignore_permissions=True)

	if frappe.get_meta(source_doctype).has_field("hr_case"):
		frappe.db.set_value(source_doctype, source_name, "hr_case", case.name, update_modified=False)

	return case.name
