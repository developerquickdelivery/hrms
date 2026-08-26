# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe import _
from frappe.model.document import Document


class QDPosition(Document):
	def validate(self):
		self._validate_reporting_line()
		self._validate_organization()

	def _validate_reporting_line(self):
		if self.reports_to_position == self.name:
			frappe.throw(_("A Position cannot report to itself."))

		parent = self.reports_to_position
		visited = {self.name}
		while parent:
			if parent in visited:
				frappe.throw(_("Reports To Position creates a circular reporting line."))
			visited.add(parent)
			parent = frappe.db.get_value("QD Position", parent, "reports_to_position")

	def _validate_organization(self):
		if self.business_unit:
			unit = frappe.db.get_value(
				"HR Business Unit",
				self.business_unit,
				["company", "branch"],
				as_dict=True,
			)
			if unit:
				if unit.company and self.company and unit.company != self.company:
					frappe.throw(_("Business Unit does not belong to the selected Company."))
				if unit.branch and self.branch and unit.branch != self.branch:
					frappe.throw(_("Business Unit does not belong to the selected Branch."))

		department = frappe.db.get_value(
			"Department",
			self.department,
			["company", "custom_qd_business_unit"],
			as_dict=True,
		)
		if department:
			if department.company and self.company and department.company != self.company:
				frappe.throw(_("Department does not belong to the selected Company."))
			if (
				department.custom_qd_business_unit
				and self.business_unit
				and department.custom_qd_business_unit != self.business_unit
			):
				frappe.throw(_("Department does not belong to the selected Business Unit."))

		if self.team:
			team_department = frappe.db.get_value("HR Team", self.team, "department")
			if team_department and team_department != self.department:
				frappe.throw(_("Team does not belong to the selected Department."))

		if self.cost_center:
			cost_center = frappe.db.get_value(
				"Cost Center",
				self.cost_center,
				["company", "custom_qd_branch", "custom_qd_business_unit", "custom_qd_department"],
				as_dict=True,
			)
			if cost_center:
				if cost_center.company and self.company and cost_center.company != self.company:
					frappe.throw(_("Cost Center does not belong to the selected Company."))
				if cost_center.custom_qd_branch and self.branch and cost_center.custom_qd_branch != self.branch:
					frappe.throw(_("Cost Center does not belong to the selected Branch."))
				if (
					cost_center.custom_qd_business_unit
					and self.business_unit
					and cost_center.custom_qd_business_unit != self.business_unit
				):
					frappe.throw(_("Cost Center does not belong to the selected Business Unit."))
				if (
					cost_center.custom_qd_department
					and cost_center.custom_qd_department != self.department
				):
					frappe.throw(_("Cost Center does not belong to the selected Department."))

