"""HR Integration Layer over ERPNext APIs, Webhooks, and managed services."""

from __future__ import annotations

import json

import frappe

WORKSPACE = "HR Integrations"

TEMPLATES = (
	("HR System Integration", "HR System", "External HR Platform", "Bidirectional", "None"),
	("SSO Integration", "SSO", "ERPNext Social Login", "Inbound", "ERPNext Managed"),
	("Email Integration", "Email", "ERPNext Email Account", "Outbound", "ERPNext Managed"),
	("SMS Integration", "SMS", "ERPNext SMS Settings", "Outbound", "ERPNext Managed"),
	("Biometrics Integration", "Biometrics", "QD Biometric Layer", "Inbound", "ERPNext Managed"),
	("Bank Integration", "Banks", "Banking Provider", "Outbound", "None"),
	("Accounting Integration", "Accounting", "ERPNext Accounting", "Bidirectional", "ERPNext Managed"),
	("Document Storage Integration", "Document Storage", "Frappe File Storage", "Bidirectional", "ERPNext Managed"),
	("Delivery Operations Integration", "Delivery Operations", "Delivery Platform", "Bidirectional", "None"),
	("External API Integration", "External APIs", "External Service", "Bidirectional", "None"),
)


def run():
	ensure_templates()
	ensure_workspace()
	frappe.clear_cache()
	return verify()


def ensure_templates():
	for name, integration_type, provider, direction, auth_type in TEMPLATES:
		if frappe.db.exists("QD HR Integration", name):
			continue
		frappe.get_doc(
			{
				"doctype": "QD HR Integration",
				"integration_name": name,
				"integration_type": integration_type,
				"provider": provider,
				"enabled": 0,
				"direction": direction,
				"connection_status": "Disabled",
				"auth_type": auth_type,
				"health_check_path": "/",
				"timeout_seconds": 30,
				"verify_ssl": 1,
				"configuration_json": "{}",
				"headers_json": "{}",
				"retry_enabled": 1,
				"max_retries": 3,
				"retry_delay_seconds": 300,
				"backoff_multiplier": 2,
			}
		).insert(ignore_permissions=True)


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
	doc.icon = "integration"
	doc.public = 1
	doc.is_hidden = 0
	doc.shortcuts = []
	doc.links = []
	doc.roles = []
	for role in ("HR Manager", "System Manager"):
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	content = [
		_block(
			"header",
			{"text": '<span class="h4"><b>HR Integration Layer</b></span>', "col": 12},
		)
	]
	for label, target, color in (
		("Integration Configurations", "QD HR Integration", "Blue"),
		("Operation Logs", "QD HR Integration Log", "Orange"),
		("Audit Trail", "QD HR Integration Audit", "Green"),
		("ERPNext Webhooks", "Webhook", "Grey"),
		("ERPNext Integration Requests", "Integration Request", "Grey"),
		("OAuth Clients", "OAuth Client", "Grey"),
	):
		if not frappe.db.exists("DocType", target):
			continue
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


def _block(block_type, data):
	return {"id": frappe.generate_hash()[:10], "type": block_type, "data": data}


def verify():
	required = {
		"QD HR Integration",
		"QD HR Integration Log",
		"QD HR Integration Audit",
	}
	missing = [doctype for doctype in required if not frappe.db.exists("DocType", doctype)]
	if missing:
		raise frappe.ValidationError(f"Missing HR Integration DocTypes: {', '.join(missing)}")
	missing_templates = [
		name for name, *_rest in TEMPLATES if not frappe.db.exists("QD HR Integration", name)
	]
	if missing_templates:
		raise frappe.ValidationError(
			f"Missing integration templates: {', '.join(missing_templates)}"
		)
	if not frappe.db.exists("Workspace", WORKSPACE):
		raise frappe.ValidationError("HR Integrations workspace missing")
	return {
		"kept": ["ERPNext REST API", "Webhook", "Integration Request"],
		"created": sorted(required),
		"templates": len(TEMPLATES),
		"retry_scheduler": "Every 5 minutes",
		"workspace": WORKSPACE,
		"verified": True,
	}
