import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today

LEVEL_SCORES = {"Low": 2, "Moderate": 3, "High": 5}
BOX_LABELS = {
	("Low", "Low"): "Underperformer",
	("Moderate", "Low"): "Effective Professional",
	("High", "Low"): "Trusted Expert",
	("Low", "Moderate"): "Inconsistent Player",
	("Moderate", "Moderate"): "Core Contributor",
	("High", "Moderate"): "High Impact Performer",
	("Low", "High"): "Potential Gem",
	("Moderate", "High"): "Emerging Talent",
	("High", "High"): "Future Leader",
}


class QDPerformanceCalibration(Document):
	def before_insert(self):
		if not self.facilitator:
			self.facilitator = frappe.session.user
		if not self.calibration_date:
			self.calibration_date = today()

	def validate(self):
		if not self.appraisals:
			frappe.throw(_("Add at least one appraisal to calibrate."))
		if not self.low_score_max:
			self.low_score_max = 2.49
		if not self.high_score_min:
			self.high_score_min = 3.75
		if flt(self.low_score_max) >= flt(self.high_score_min):
			frappe.throw(_("Low Score Maximum must be less than High Score Minimum."))
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
			if not 0 <= flt(row.calibrated_score) <= 5:
				frappe.throw(_("Calibrated Score for {0} must be between 0 and 5.").format(row.employee_name))
			if not 1 <= flt(row.potential_score) <= 5:
				frappe.throw(_("Potential Score for {0} must be between 1 and 5.").format(row.employee_name))
			row.performance_level = self._level(row.calibrated_score)
			row.potential_level = self._level(row.potential_score)
			row.nine_box = BOX_LABELS[(row.performance_level, row.potential_level)]
			if row.retention_risk == "High" and not row.development_action:
				frappe.throw(
					_("Development / Succession Action is required for high retention risk employee {0}.").format(
						row.employee_name
					)
				)

	def _level(self, score):
		score = flt(score)
		low_max = flt(self.low_score_max or 2.49)
		high_min = flt(self.high_score_min or 3.75)
		if score <= low_max:
			return "Low"
		if score >= high_min:
			return "High"
		return "Moderate"

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
					"custom_qd_potential_score": flt(row.potential_score),
					"custom_qd_nine_box_placement": row.nine_box,
					"custom_qd_calibration": self.name,
					"custom_qd_rating_band": row.rating_band,
				},
			)
