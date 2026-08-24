"""Verification script for Quick Delivery organizational setup and workflows.

Run via:
    bench --site <site> execute qd_hrms.setup.verify_org.run
"""

from __future__ import annotations

import frappe

COMPANY = "Quick Delivery"


def run():
	abbr = frappe.db.get_value("Company", COMPANY, "abbr") or "QD"
	print("\n========================================================")
	print("  QUICK DELIVERY ORGANIZATIONAL SETUP VERIFICATION")
	print("========================================================\n")

	# 1. Company
	company_doc = frappe.get_doc("Company", COMPANY)
	print(f"[✓] Company: {company_doc.name} (Abbr: {company_doc.abbr}, Currency: {company_doc.default_currency}, Country: {company_doc.country})")

	# 2. Departments
	active_depts = frappe.get_all(
		"Department",
		filters={"company": COMPANY, "disabled": 0},
		pluck="name",
		order_by="name",
	)
	disabled_depts = frappe.get_all(
		"Department",
		filters={"company": COMPANY, "disabled": 1},
		pluck="name",
	)
	print(f"\n[✓] Active Departments ({len(active_depts)}):")
	for dept in active_depts:
		print(f"    - {dept}")
	print(f"    (Disabled default sample departments: {len(disabled_depts)})")

	# 3. Employee Grades
	grades = frappe.get_all(
		"Employee Grade",
		fields=["name", "custom_qd_grade_code", "custom_qd_grade_level", "custom_qd_grade_category", "custom_qd_is_active"],
		order_by="custom_qd_grade_level",
	)
	print(f"\n[✓] Employee Grades ({len(grades)}):")
	for g in grades:
		print(f"    - [{g.custom_qd_grade_code}] {g.name} (Level: {g.custom_qd_grade_level}, Category: {g.custom_qd_grade_category})")

	# 4. Designations
	active_desigs = frappe.get_all(
		"Designation",
		filters={"custom_qd_is_active": 1},
		fields=["name", "custom_qd_default_employee_grade", "custom_qd_eligible_for_acting"],
		order_by="name",
	)
	disabled_desigs = frappe.get_all(
		"Designation",
		filters={"custom_qd_is_active": 0},
		pluck="name",
	)
	print(f"\n[✓] Active QD Designations ({len(active_desigs)}):")
	for d in active_desigs:
		acting_str = " [Acting Eligible]" if d.custom_qd_eligible_for_acting else ""
		grade_str = f" -> {d.custom_qd_default_employee_grade}" if d.custom_qd_default_employee_grade else ""
		print(f"    - {d.name}{grade_str}{acting_str}")
	print(f"    (Disabled default sample designations: {len(disabled_desigs)})")

	# 5. QD Positions & Hierarchy
	positions = frappe.get_all(
		"QD Position",
		fields=["name", "position_code", "department", "designation", "employee_grade", "reports_to_position"],
		order_by="department, position_code",
	)
	print(f"\n[✓] QD Headcount Positions ({len(positions)}):")
	for p in positions:
		reports_str = f" (Reports To: {p.reports_to_position})" if p.reports_to_position else " [Top Level]"
		print(f"    - [{p.position_code}] {p.name} | {p.department} | {p.employee_grade}{reports_str}")

	# 6. Leave Workflow
	if frappe.db.exists("Workflow", "QD Leave Application Approval"):
		wf = frappe.get_doc("Workflow", "QD Leave Application Approval")
		print(f"\n[✓] Leave Workflow: '{wf.name}' (Active: {wf.is_active})")
		print("    States:")
		for s in wf.states:
			print(f"      * {s.state} (DocStatus: {s.doc_status}, Allow Edit: {s.allow_edit})")
		print("    Transitions:")
		for t in wf.transitions:
			print(f"      * {t.state} --[{t.action}]--> {t.next_state} (Role: {t.allowed})")

	print("\n========================================================")
	print("  ORGANIZATIONAL STRUCTURE SUMMARY")
	print(f"  * Company: {COMPANY}")
	print(f"  * Active Departments: {len(active_depts)}")
	print(f"  * Employee Grades: {len(grades)}")
	print(f"  * Active Designations: {len(active_desigs)}")
	print(f"  * Headcount Positions: {len(positions)}")
	print("========================================================\n")
	return {
		"departments": len(active_depts),
		"grades": len(grades),
		"designations": len(active_desigs),
		"positions": len(positions),
	}
