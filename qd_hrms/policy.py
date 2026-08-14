"""Policy acknowledgement helpers: issue before day one and block employee creation."""

from __future__ import annotations

import frappe
from frappe import _


def on_onboarding_submit(doc, method=None):
	issue_acknowledgements(doc)


def validate_onboarding(doc, method=None):
	if doc.boarding_status == "Completed":
		assert_required_signed(job_applicant=doc.job_applicant, employee=doc.employee)


def validate_before_employee_insert(doc, method=None):
	if not doc.get("job_applicant"):
		return
	assert_required_signed(job_applicant=doc.job_applicant, employee=None)


def issue_acknowledgements(onboarding):
	policies = frappe.get_all(
		"QD Policy",
		filters={"is_active": 1, "must_acknowledge_before_joining": 1},
		pluck="name",
	)
	created = []
	for policy in policies:
		filters = {
			"policy": policy,
			"docstatus": ["<", 2],
		}
		if onboarding.job_applicant:
			filters["job_applicant"] = onboarding.job_applicant
		elif onboarding.employee:
			filters["employee"] = onboarding.employee
		else:
			continue
		if frappe.db.exists("QD Policy Acknowledgement", filters):
			continue
		ack = frappe.get_doc(
			{
				"doctype": "QD Policy Acknowledgement",
				"policy": policy,
				"job_applicant": onboarding.job_applicant,
				"employee": onboarding.employee,
				"employee_onboarding": onboarding.name,
				"company": onboarding.company,
				"employee_name": onboarding.employee_name,
				"status": "Draft",
			}
		)
		ack.insert(ignore_permissions=True)
		created.append(ack.name)
	if created:
		frappe.msgprint(
			_("Issued {0} policy acknowledgement(s) to sign before day one.").format(len(created)),
			alert=True,
		)
	return created


def unsigned_required(job_applicant=None, employee=None):
	policies = frappe.get_all(
		"QD Policy",
		filters={"is_active": 1, "must_acknowledge_before_joining": 1},
		pluck="name",
	)
	missing = []
	for policy in policies:
		filters = {"policy": policy, "docstatus": 1}
		if job_applicant:
			filters["job_applicant"] = job_applicant
		elif employee:
			filters["employee"] = employee
		else:
			continue
		if not frappe.db.exists("QD Policy Acknowledgement", filters):
			missing.append(policy)
	return missing


def assert_required_signed(job_applicant=None, employee=None):
	missing = unsigned_required(job_applicant=job_applicant, employee=employee)
	if missing:
		frappe.throw(
			_(
				"Sign these policies before day one (e-signature required): {0}"
			).format(", ".join(missing))
		)


@frappe.whitelist()
def issue_for_onboarding(onboarding):
	doc = frappe.get_doc("Employee Onboarding", onboarding)
	return issue_acknowledgements(doc)
