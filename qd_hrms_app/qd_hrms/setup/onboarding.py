"""Employee Onboarding template: orientation + account/workspace readiness."""

from __future__ import annotations

import frappe
from frappe.utils import today

TEMPLATE_TITLE = "QD Standard Onboarding"

ACCOUNT_TASKS = [
	(
		"Create Desk user and assign HR/employee roles",
		"HR User",
		0,
		1,
		1,
		"Create the ERPNext user, set a temporary password, and assign Employee / relevant roles.",
	),
	(
		"Provision company email and verify login",
		"HR User",
		0,
		1,
		1,
		"Create mailbox (if used), send credentials, and confirm the person can sign in to Desk.",
	),
	(
		"Assign workspace and module access",
		"HR User",
		0,
		1,
		1,
		"Set default workspace (Employee Dashboard) and hide unused ERP modules.",
	),
	(
		"Collect signed policy acknowledgements (before day one)",
		"HR User",
		0,
		1,
		1,
		"Open QD Policy Acknowledgement records, have the hire read each policy, draw e-signature, and Submit.",
	),
]

ORIENTATION_TASKS = [
	(
		"Day-1 orientation: company overview",
		"HR User",
		0,
		1,
		0,
		"Welcome, Quick Delivery values, org chart, and how hubs/dispatch work.",
	),
	(
		"Safety and delivery standards briefing",
		"HR User",
		0,
		1,
		0,
		"PPE, riding/driving rules, incident reporting, and customer conduct.",
	),
	(
		"Meet reporting manager",
		"HR User",
		0,
		1,
		0,
		"Introduce reports_to manager, shift expectations, and first-week goals.",
	),
	(
		"Role-specific orientation",
		"HR User",
		1,
		2,
		0,
		"Rider / dispatcher / hub / office walkthrough of tools and SOPs.",
	),
	(
		"Workspace login check on day one",
		"HR User",
		0,
		1,
		0,
		"Confirm Desk + email access on the first working day.",
	),
]


def run():
	ensure_policies()
	template = ensure_template()
	return {
		"template": template,
		"policies": frappe.get_all("QD Policy", filters={"is_active": 1}, pluck="name"),
	}


def ensure_template():
	name = frappe.db.get_value("Employee Onboarding Template", {"title": TEMPLATE_TITLE}, "name")
	if name:
		doc = frappe.get_doc("Employee Onboarding Template", name)
		doc.activities = []
	else:
		doc = frappe.new_doc("Employee Onboarding Template")
		doc.title = TEMPLATE_TITLE

	company = frappe.defaults.get_defaults().get("company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if company:
		doc.company = company

	for activity_name, role, begin_on, duration, required, description in ACCOUNT_TASKS + ORIENTATION_TASKS:
		doc.append(
			"activities",
			{
				"activity_name": activity_name,
				"role": role if frappe.db.exists("Role", role) else None,
				"begin_on": begin_on,
				"duration": duration,
				"required_for_employee_creation": required,
				"task_weight": 1,
				"description": description,
			},
		)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.name


def ensure_policies():
	defaults = [
		(
			"Code of Conduct",
			"<h3>Quick Delivery — Code of Conduct</h3>"
			"<p>Treat customers, riders, and colleagues with respect. Follow dispatch instructions, "
			"protect company property, and report incidents immediately.</p>"
			"<p>Violations may result in disciplinary action up to termination.</p>",
		),
		(
			"Confidentiality and Data Protection",
			"<h3>Confidentiality and Data Protection</h3>"
			"<p>Do not share customer addresses, phone numbers, order details, or internal systems access "
			"with anyone outside Quick Delivery. Use Desk only for assigned work.</p>",
		),
		(
			"Health, Safety and Road Rules",
			"<h3>Health, Safety and Road Rules</h3>"
			"<p>Wear required PPE, follow traffic laws, do not ride/drive under the influence, "
			"and stop work if conditions are unsafe. Report accidents the same day.</p>",
		),
	]
	for title, body in defaults:
		if frappe.db.exists("QD Policy", title):
			continue
		frappe.get_doc(
			{
				"doctype": "QD Policy",
				"title": title,
				"version": "1.0",
				"is_active": 1,
				"must_acknowledge_before_joining": 1,
				"requires_signature": 1,
				"effective_from": today(),
				"policy_body": body,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
