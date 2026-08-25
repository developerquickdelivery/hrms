import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class QDRatingScale(Document):
	def validate(self):
		if flt(self.min_score) >= flt(self.max_score):
			frappe.throw(_("Minimum Score must be less than Maximum Score."))
		if not self.levels:
			frappe.throw(_("Add at least one rating level."))
		scores = []
		for row in self.levels:
			if not (flt(self.min_score) <= flt(row.score) <= flt(self.max_score)):
				frappe.throw(_("Level score {0} must be within the scale range.").format(row.score))
			scores.append(flt(row.score))
		if len(scores) != len(set(scores)):
			frappe.throw(_("Each level score must be unique."))
		if self.is_default:
			for name in frappe.get_all(
				"QD Rating Scale",
				filters={"is_default": 1, "name": ["!=", self.name or ""]},
				pluck="name",
			):
				frappe.db.set_value("QD Rating Scale", name, "is_default", 0)
