"""Employee asset custody setup on top of ERPNext Asset."""

from __future__ import annotations

import json

import frappe

WORKSPACE = "Employee Assets"


def run():
	ensure_workspace()
	extend_ess()
	frappe.clear_cache()
	return verify()


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
	doc.icon = "assets"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("HR User", "HR Manager", "Asset Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})

	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>Employee Assets</b></span>', "col": 12},
		)
	]
	for label, target, color in (
		("Assets", "Asset", "Blue"),
		("Employee Asset Assignments", "QD Employee Asset Assignment", "Blue"),
		("Loss / Damage Cases", "QD Asset Loss Damage Case", "Red"),
		("Asset Recoveries", "QD Asset Recovery", "Green"),
	):
		doc.append(
			"shortcuts",
			{
				"type": "DocType",
				"link_to": target,
				"doc_view": "List",
				"label": label,
				"color": color,
			},
		)
		content.append(_block("shortcut", {"shortcut_name": label, "col": 3}))
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
			"Asset": ["read"],
			"QD Employee Asset Assignment": ["read"],
			"QD Asset Loss Damage Case": ["read", "write", "create"],
			"QD Asset Recovery": ["read"],
		},
		doc,
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {
		"QD Employee Asset Assignment",
		"QD Asset Loss Damage Case",
		"QD Asset Recovery",
	}
	missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]
	if missing:
		raise frappe.ValidationError(f"Missing Employee Asset DocTypes: {', '.join(missing)}")
	if not frappe.db.exists("DocType", "Asset"):
		raise frappe.ValidationError("ERPNext Asset DocType is unavailable")
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("Employee Assets workspace missing")
	return {
		"kept": ["Asset"],
		"created": sorted(required),
		"workspace": WORKSPACE,
		"verified": True,
	}
