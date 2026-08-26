import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class QDExitClearance(Document):
	def validate(self):
		if not self.clearance_items:
			frappe.throw(_("At least one clearance task is required."))
		for row in self.clearance_items:
			if row.status == "Exception" and not row.remarks:
				frappe.throw(
					_("Remarks are required for exception in {0}.").format(
						row.clearance_department
					)
				)
			if row.status in ("Cleared", "Exception") and not row.cleared_on:
				row.cleared_by = frappe.session.user
				row.cleared_on = now()
			elif row.status not in ("Cleared", "Exception"):
				row.cleared_by = None
				row.cleared_on = None
		self._set_clearance_status()

	def after_insert(self):
		self._create_tasks()

	def on_update(self):
		self._sync_tasks()
		if self.clearance_status == "Completed":
			frappe.db.set_value(
				"Employee Separation",
				self.employee_separation,
				"custom_qd_lifecycle_status",
				"Final Payroll",
				update_modified=False,
			)

	def _set_clearance_status(self):
		statuses = [row.status for row in self.clearance_items]
		if statuses and all(status in ("Cleared", "Exception") for status in statuses):
			self.clearance_status = "Completed"
			if not self.completed_on:
				self.completed_by = frappe.session.user
				self.completed_on = now()
		elif any(status != "Pending" for status in statuses):
			self.clearance_status = "In Progress"
		else:
			self.clearance_status = "Open"

	def _create_tasks(self):
		for row in self.clearance_items:
			if row.task:
				continue
			task = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": f"Exit clearance - {row.clearance_department} - {self.employee_name}",
					"description": row.clearance_item,
					"exp_end_date": self.due_date,
					"custom_qd_exit_clearance": self.name,
					"custom_qd_clearance_department": row.clearance_department,
				}
			).insert(ignore_permissions=True)
			frappe.db.set_value(
				"QD Exit Clearance Item", row.name, "task", task.name, update_modified=False
			)
			if row.responsible_user:
				_create_assignment(task.name, row.responsible_user, row.clearance_item)

	def _sync_tasks(self):
		task_status = {
			"Pending": "Open",
			"In Progress": "Working",
			"Cleared": "Completed",
			"Exception": "Completed",
		}
		for row in self.clearance_items:
			if not row.task or not frappe.db.exists("Task", row.task):
				continue
			expected = task_status[row.status]
			if frappe.db.get_value("Task", row.task, "status") != expected:
				frappe.db.set_value("Task", row.task, "status", expected)


def _create_assignment(task, user, description):
	if frappe.db.exists(
		"ToDo",
		{
			"reference_type": "Task",
			"reference_name": task,
			"allocated_to": user,
			"status": "Open",
		},
	):
		return
	frappe.get_doc(
		{
			"doctype": "ToDo",
			"allocated_to": user,
			"reference_type": "Task",
			"reference_name": task,
			"description": description,
		}
	).insert(ignore_permissions=True)
