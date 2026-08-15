import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from qd_hrms.qd_hrms.doctype.qd_hr_case.qd_hr_case import make_hr_case


class QDDisciplinaryCase(Document):
	def before_insert(self):
		if not self.reported_by:
			self.reported_by = frappe.session.user

	def validate(self):
		if self.incident_date and getdate(self.incident_date) > getdate(nowdate()):
			frappe.throw(_("Incident Date cannot be in the future."))

	def on_submit(self):
		case = make_hr_case("QD Disciplinary Case", self.name)
		self.db_set("hr_case", case, update_modified=False)

	def before_cancel(self):
		if self.hr_case and frappe.db.get_value("QD HR Case", self.hr_case, "docstatus") == 1:
			frappe.throw(
				_("Cannot cancel: linked HR Case {0} is already closed. Cancel the HR Case first.").format(
					self.hr_case
				)
			)
