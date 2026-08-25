import frappe
from frappe.model.document import Document


class QDTrainingAttendance(Document):
	def before_insert(self):
		self.recorded_by = frappe.session.user

	def validate(self):
		duplicate = frappe.db.exists(
			"QD Training Attendance",
			{
				"enrollment": self.enrollment,
				"attendance_date": self.attendance_date,
				"name": ("!=", self.name or ""),
			},
		)
		if duplicate:
			frappe.throw("Attendance is already recorded for this date.")

	def on_update(self):
		total = frappe.db.count("QD Training Attendance", {"enrollment": self.enrollment})
		present = frappe.db.count(
			"QD Training Attendance",
			{"enrollment": self.enrollment, "attendance_status": ("in", ("Present", "Late"))},
		)
		if total:
			frappe.db.set_value(
				"QD Training Enrollment",
				self.enrollment,
				"attendance_percentage",
				present * 100 / total,
			)
