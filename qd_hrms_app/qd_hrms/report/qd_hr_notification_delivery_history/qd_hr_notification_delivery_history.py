import frappe
from frappe import _
from frappe.utils import add_days, getdate, today


HR_DOCTYPES = (
	"Employee",
	"QD Employee Document",
	"Leave Application",
	"Payroll Entry",
	"Employee Separation",
	"QD Employee Request",
	"QD HR Case",
	"QD Training Certification",
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date = getdate(filters.from_date or add_days(today(), -30))
	to_date = getdate(filters.to_date or today())
	columns = [
		{"label": _("Channel"), "fieldname": "channel", "fieldtype": "Data", "width": 90},
		{"label": _("Date"), "fieldname": "delivery_date", "fieldtype": "Datetime", "width": 150},
		{"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 240},
		{"label": _("Recipient"), "fieldname": "recipient", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Reference Type"), "fieldname": "reference_doctype", "fieldtype": "Link", "options": "DocType", "width": 160},
		{"label": _("Reference"), "fieldname": "reference_name", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 160},
	]
	data = []
	if filters.channel in (None, "", "In-app"):
		data.extend(_in_app_rows(from_date, to_date, filters.status))
	if filters.channel in (None, "", "Email"):
		data.extend(_email_rows(from_date, to_date, filters.status))
	data.sort(key=lambda row: row.get("delivery_date") or "", reverse=True)
	return columns, data


def _in_app_rows(from_date, to_date, status=None):
	conditions = {
		"creation": ["between", [from_date, add_days(to_date, 1)]],
		"document_type": ["in", HR_DOCTYPES],
	}
	if status:
		conditions["read"] = 1 if status.lower() == "read" else 0
	rows = frappe.get_all(
		"Notification Log",
		fields=[
			"creation as delivery_date",
			"subject",
			"for_user as recipient",
			"read",
			"document_type as reference_doctype",
			"document_name as reference_name",
		],
		filters=conditions,
		ignore_permissions=True,
	)
	for row in rows:
		row.channel = "In-app"
		row.status = "Read" if row.read else "Unread"
	return rows


def _email_rows(from_date, to_date, status=None):
	conditions = {
		"creation": ["between", [from_date, add_days(to_date, 1)]],
		"reference_doctype": ["in", HR_DOCTYPES],
	}
	if status:
		conditions["status"] = status
	rows = frappe.get_all(
		"Email Queue",
		fields=[
			"name",
			"creation as delivery_date",
			"status",
			"reference_doctype",
			"reference_name",
		],
		filters=conditions,
		ignore_permissions=True,
	)
	for row in rows:
		row.channel = "Email"
		row.subject = frappe.db.get_value(
			"Communication", {"name": frappe.db.get_value("Email Queue", row.name, "communication")}, "subject"
		) or _("HR Notification")
		row.recipient = ", ".join(
			frappe.get_all(
				"Email Queue Recipient",
				filters={"parent": row.name},
				pluck="recipient",
				ignore_permissions=True,
			)
		)
	return rows
