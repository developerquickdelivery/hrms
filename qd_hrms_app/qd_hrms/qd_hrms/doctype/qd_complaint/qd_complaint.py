import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from qd_hrms.qd_hrms.doctype.qd_hr_case.qd_hr_case import make_hr_case


class QDComplaint(Document):
	def before_insert(self):
		if not self.complaint_date:
			self.complaint_date = nowdate()

	def validate(self):
		if self.complaint_date and getdate(self.complaint_date) > getdate(nowdate()):
			frappe.throw(_("Complaint Date cannot be in the future."))
		if self.against_employee and self.against_employee == self.employee:
			frappe.throw(_("A complaint cannot be filed against the complainant themselves."))

	def on_submit(self):
		case = make_hr_case("QD Complaint", self.name)
		self.db_set("hr_case", case, update_modified=False)

	def before_cancel(self):
		if self.hr_case and frappe.db.get_value("QD HR Case", self.hr_case, "docstatus") == 1:
			frappe.throw(
				_("Cannot cancel: linked HR Case {0} is already closed. Cancel the HR Case first.").format(
					self.hr_case
				)
			)
