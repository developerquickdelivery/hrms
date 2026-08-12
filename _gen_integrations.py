#!/usr/bin/env python3
"""Generate 2.18 Integrations DocTypes for qd_hrms."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/qd/frappe-bench/apps/qd_hrms/qd_hrms/quick_delivery_hrms/doctype")
MODULE = "Quick Delivery HRMS"

PERMS_FULL = [
	{"role": "System Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "HR Manager", "create": 1, "read": 1, "write": 1, "delete": 1, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
	{"role": "QD HR Officer", "create": 1, "read": 1, "write": 1, "delete": 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1},
]

INTEGRATION_TYPES = (
	"Identity / SSO\nEmail Gateway\nSMS Gateway\nBiometric Device\n"
	"Finance / Accounting\nBank Export\nDocument Storage\n"
	"Delivery Operations\nREST API\nWebhook"
)


def slug(name: str) -> str:
	return name.lower().replace(" ", "_")


def write_doctype(name: str, payload: dict, py_extra: str = "pass"):
	folder = ROOT / slug(name)
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").write_text("", encoding="utf-8")
	class_name = name.replace(" ", "")
	(folder / f"{slug(name)}.py").write_text(
		f"""# Copyright (c) 2026, Quick Delivery Service and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class {class_name}(Document):
	{py_extra}
""",
		encoding="utf-8",
	)
	doc = {
		"actions": [],
		"creation": "2026-08-11 00:00:00.000000",
		"doctype": "DocType",
		"engine": "InnoDB",
		"index_web_pages_for_search": 1,
		"links": [],
		"modified": "2026-08-11 00:00:00.000000",
		"modified_by": "Administrator",
		"module": MODULE,
		"name": name,
		"owner": "Administrator",
		"sort_field": "modified",
		"sort_order": "DESC",
		"states": [],
		"track_changes": 1,
		**payload,
	}
	(folder / f"{slug(name)}.json").write_text(
		json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
	)
	print("wrote", name)


write_doctype(
	"QD Integration Endpoint",
	{
		"allow_rename": 1,
		"autoname": "field:endpoint_name",
		"naming_rule": "By fieldname",
		"permissions": PERMS_FULL,
		"search_fields": "endpoint_name,integration_type,base_url",
		"field_order": [
			"endpoint_name", "integration_type", "is_active", "column_break_1",
			"base_url", "auth_type", "api_key",
			"section_link", "linked_doctype", "linked_name",
			"description", "remarks",
		],
		"fields": [
			{"fieldname": "endpoint_name", "fieldtype": "Data", "label": "Endpoint Name", "reqd": 1, "unique": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "integration_type", "fieldtype": "Select", "label": "Integration Type", "options": INTEGRATION_TYPES, "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "in_list_view": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "base_url", "fieldtype": "Data", "label": "Base URL"},
			{"fieldname": "auth_type", "fieldtype": "Select", "label": "Auth Type", "options": "\nNone\nAPI Key\nOAuth\nBasic\nWebhook Secret"},
			{"fieldname": "api_key", "fieldtype": "Password", "label": "API Key / Secret"},
			{"fieldname": "section_link", "fieldtype": "Section Break", "label": "Linked Record"},
			{"fieldname": "linked_doctype", "fieldtype": "Link", "label": "Linked DocType", "options": "DocType"},
			{"fieldname": "linked_name", "fieldtype": "Dynamic Link", "label": "Linked Name", "options": "linked_doctype"},
			{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
			{"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
		],
	},
)

write_doctype(
	"QD Webhook Event Log",
	{
		"allow_rename": 0,
		"autoname": "naming_series:",
		"naming_rule": 'By "Naming Series" field',
		"permissions": PERMS_FULL,
		"search_fields": "event_type,direction,status,reference_name",
		"field_order": [
			"naming_series", "direction", "event_type", "status",
			"column_break_1", "received_on", "processed_on",
			"integration_endpoint", "source_ip",
			"section_reference", "reference_doctype", "reference_name",
			"section_payload", "payload", "error_message",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-WHK-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "direction", "fieldtype": "Select", "label": "Direction", "options": "Inbound\nOutbound", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "event_type", "fieldtype": "Data", "label": "Event Type", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Received\nProcessed\nFailed\nIgnored", "default": "Received", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "received_on", "fieldtype": "Datetime", "label": "Received On", "default": "Now", "in_list_view": 1},
			{"fieldname": "processed_on", "fieldtype": "Datetime", "label": "Processed On"},
			{"fieldname": "integration_endpoint", "fieldtype": "Link", "label": "Integration Endpoint", "options": "QD Integration Endpoint"},
			{"fieldname": "source_ip", "fieldtype": "Data", "label": "Source IP"},
			{"fieldname": "section_reference", "fieldtype": "Section Break", "label": "Reference"},
			{"fieldname": "reference_doctype", "fieldtype": "Link", "label": "Reference DocType", "options": "DocType"},
			{"fieldname": "reference_name", "fieldtype": "Dynamic Link", "label": "Reference Name", "options": "reference_doctype", "in_list_view": 1},
			{"fieldname": "section_payload", "fieldtype": "Section Break", "label": "Payload"},
			{"fieldname": "payload", "fieldtype": "Code", "label": "Payload", "options": "JSON"},
			{"fieldname": "error_message", "fieldtype": "Small Text", "label": "Error Message"},
		],
	},
)

write_doctype(
	"QD Biometric Sync Log",
	{
		"allow_rename": 0,
		"autoname": "naming_series:",
		"naming_rule": 'By "Naming Series" field',
		"permissions": PERMS_FULL,
		"search_fields": "biometric_device,status",
		"field_order": [
			"naming_series", "biometric_device", "status",
			"column_break_1", "sync_started", "sync_completed",
			"punches_received", "checkins_created", "error_message",
		],
		"fields": [
			{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": "QD-BIO-.YYYY.-.#####", "reqd": 1},
			{"fieldname": "biometric_device", "fieldtype": "Link", "label": "Biometric Device", "options": "QD Biometric Device", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Success\nPartial\nFailed", "default": "Success", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "column_break_1", "fieldtype": "Column Break"},
			{"fieldname": "sync_started", "fieldtype": "Datetime", "label": "Sync Started", "default": "Now"},
			{"fieldname": "sync_completed", "fieldtype": "Datetime", "label": "Sync Completed"},
			{"fieldname": "punches_received", "fieldtype": "Int", "label": "Punches Received", "default": "0"},
			{"fieldname": "checkins_created", "fieldtype": "Int", "label": "Check-ins Created", "default": "0"},
			{"fieldname": "error_message", "fieldtype": "Small Text", "label": "Error Message"},
		],
	},
)

print("done")
