import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class QDPerformanceCalibration(Document):
	def before_insert(self):
		if not self.facilitator:
			self.facilitator = frappe.session.user
		if not self.calibration_date:
			self.calibration_date = today()

	def validate(self):
		if not self.appraisals:
			frappe.throw(_("Add at least one appraisal to calibrate."))
		seen = set()
		for row in self.appraisals:
			if row.appraisal in seen:
				frappe.throw(_("Appraisal {0} is listed more than once.").format(row.appraisal))
			seen.add(row.appraisal)
			cycle = frappe.db.get_value("Appraisal", row.appraisal, "appraisal_cycle")
			if cycle != self.appraisal_cycle:
				frappe.throw(
					_("Appraisal {0} does not belong to cycle {1}.").format(
						row.appraisal, self.appraisal_cycle
					)
				)

	def before_submit(self):
		if self.approval_status != "Completed":
			frappe.throw(_("Mark calibration as Completed through the workflow before submission."))

	def on_submit(self):
		for row in self.appraisals:
			frappe.db.set_value(
				"Appraisal",
				row.appraisal,
				{
					"custom_qd_calibrated_score": flt(row.calibrated_score),
					"custom_qd_calibration": self.name,
					"custom_qd_rating_band": row.rating_band,
				},
			)
