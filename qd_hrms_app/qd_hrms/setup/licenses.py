"""License and certification auto-renewal setup on top of native Notifications."""

from __future__ import annotations

import json

import frappe

from qd_hrms.licenses import REQUEST_TYPE, _ensure_request_type

WORKSPACE = "License Compliance"


def run():
	_ensure_request_type()
	ensure_license_types()
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


def ensure_license_types():
	types = (
		{
			"license_type": "Driving License",
			"category": "License",
			"issuing_authority": "Transport Authority",
			"default_validity_days": 365,
			"renewal_lead_days": 30,
			"auto_renew_default": 1,
			"required_for_work": 1,
			"requires_attachment": 1,
			"description": "Valid driving license required for riders and drivers.",
		},
		{
			"license_type": "Work Permit",
			"category": "Permit",
			"issuing_authority": "Immigration / Labour Authority",
			"default_validity_days": 365,
			"renewal_lead_days": 60,
			"auto_renew_default": 1,
			"required_for_work": 1,
			"requires_attachment": 1,
			"description": "Residence or work authorization that must remain current.",
		},
		{
			"license_type": "Rider Safety Certification",
			"category": "Safety",
			"issuing_authority": "Quick Delivery Training",
			"default_validity_days": 365,
			"renewal_lead_days": 90,
			"auto_renew_default": 1,
			"required_for_work": 1,
			"requires_attachment": 0,
			"linked_course": "Rider Safety Induction"
			if frappe.db.exists("QD Training Course", "Rider Safety Induction")
			else None,
			"description": "Mandatory rider safety certification with annual refresh.",
		},
		{
			"license_type": "Professional Certification",
			"category": "Professional",
			"issuing_authority": "External Body",
			"default_validity_days": 730,
			"renewal_lead_days": 60,
			"auto_renew_default": 1,
			"required_for_work": 0,
			"requires_attachment": 1,
			"description": "Role-specific professional or trade certification.",
		},
	)
	for values in types:
		name = values["license_type"]
		doc = (
			frappe.get_doc("QD License Type", name)
			if frappe.db.exists("QD License Type", name)
			else frappe.new_doc("QD License Type")
		)
		doc.update(values)
		doc.is_active = 1
		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)


def ensure_workspace():
	doc = (
		frappe.get_doc("Workspace", WORKSPACE)
		if frappe.db.exists("Workspace", WORKSPACE)
		else frappe.new_doc("Workspace")
	)
	if doc.is_new():
		doc.label = WORKSPACE
	doc.title = WORKSPACE
	doc.module = "QD HRMS"
	doc.icon = "ok"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("Employee", "HR User", "HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>License & Certification Compliance</b></span>', "col": 12},
		)
	]
	for label, target, view, color in (
		("License Types", "QD License Type", "List", "Blue"),
		("Employee Licenses", "QD Employee License", "List", "Orange"),
		("Renewal Requests", "QD Employee Request", "List", "Orange"),
		("Training Certifications", "QD Training Certification", "List", "Green"),
		("Compliance Report", "QD Compliance Report", "Report", "Red"),
		("License Renewal Report", "QD License Renewal Report", "Report", "Red"),
	):
		if view == "Report" and not frappe.db.exists("Report", target):
			continue
		if view != "Report" and not frappe.db.exists("DocType", target):
			continue
		doc.append(
			"shortcuts",
			{"type": "DocType" if view != "Report" else "Report", "link_to": target, "doc_view": "List", "label": label, "color": color},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 4}))
	doc.content = json.dumps(content)
	doc.flags.ignore_links = True
	was_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_install = was_install


def extend_ess():
	if not frappe.db.exists("User Type", "Employee Self Service"):
		return
	from hrms.setup import append_docperms_to_user_type

	doc = frappe.get_doc("User Type", "Employee Self Service")
	append_docperms_to_user_type(
		{
			"QD License Type": ["read"],
			"QD Employee License": ["read"],
		},
		doc,
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {"QD License Type", "QD Employee License"}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing DocTypes: {', '.join(missing)}")
	if not frappe.db.exists("QD Employee Request Type", REQUEST_TYPE):
		raise frappe.ValidationError("License Renewal request type missing")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("License Compliance workspace missing")
	for name in ("Driving License", "Work Permit"):
		if not frappe.db.exists("QD License Type", name):
			raise frappe.ValidationError(f"Missing license type: {name}")
	return {
		"created": sorted(required),
		"request_type": REQUEST_TYPE,
		"workspace": WORKSPACE,
		"alerts": ["30 days", "7 days", "expiry escalation"],
		"verified": True,
	}
