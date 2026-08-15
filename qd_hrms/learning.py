from __future__ import annotations

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
from frappe.utils import date_diff, now_datetime, today


def validate_training_event(doc, method=None):
	if doc.get("custom_qd_course"):
		doc.course = doc.custom_qd_course
	if doc.get("custom_qd_capacity") and len(doc.get("employees") or []) > doc.custom_qd_capacity:
		frappe.throw(_("Training Session capacity has been exceeded."))


def sync_session_enrollments(doc, method=None):
	"""Keep standard Training Event attendees linked to dedicated enrollments."""
	course = doc.get("custom_qd_course")
	if not course:
		return
	for row in doc.get("employees") or []:
		if not row.employee:
			continue
		enrollment = frappe.db.exists(
			"QD Training Enrollment",
			{
				"employee": row.employee,
				"training_session": doc.name,
				"status": ("not in", ("Withdrawn", "Cancelled")),
			},
		)
		if not enrollment:
			frappe.get_doc(
				{
					"doctype": "QD Training Enrollment",
					"employee": row.employee,
					"course": course,
					"training_program": doc.training_program,
					"training_session": doc.name,
				}
			).insert(ignore_permissions=True)


def process_certification_expiry_notifications():
	"""Issue one notification at 90, 30, 7 days and once after expiry."""
	for cert in frappe.get_all(
		"QD Training Certification",
		filters={"status": ("!=", "Revoked")},
		fields=[
			"name",
			"employee",
			"employee_name",
			"course",
			"expiry_date",
			"notification_90_sent",
			"notification_30_sent",
			"notification_7_sent",
			"expired_notification_sent",
		],
	):
		days = date_diff(cert.expiry_date, today())
		fieldname = None
		label = None
		if days < 0 and not cert.expired_notification_sent:
			fieldname, label = "expired_notification_sent", _("Expired")
		elif 0 <= days <= 7 and not cert.notification_7_sent:
			fieldname, label = "notification_7_sent", _("7 days before expiry")
		elif 7 < days <= 30 and not cert.notification_30_sent:
			fieldname, label = "notification_30_sent", _("30 days before expiry")
		elif 30 < days <= 90 and not cert.notification_90_sent:
			fieldname, label = "notification_90_sent", _("90 days before expiry")

		updates = {
			"days_to_expiry": days,
			"status": "Expired" if days < 0 else "Active",
		}
		if fieldname:
			_notify_certificate(cert, days, label)
			updates[fieldname] = 1
			updates["last_notification_on"] = now_datetime()
		frappe.db.set_value("QD Training Certification", cert.name, updates, update_modified=False)


def _notify_certificate(cert, days, label):
	employee = frappe.db.get_value(
		"Employee", cert.employee, ["user_id", "reports_to"], as_dict=True
	)
	users = [employee.user_id] if employee and employee.user_id else []
	if employee and employee.reports_to:
		manager_user = frappe.db.get_value("Employee", employee.reports_to, "user_id")
		if manager_user:
			users.append(manager_user)
	users.extend(
		frappe.get_all(
			"Has Role",
			filters={"role": "HR Manager", "parenttype": "User"},
			pluck="parent",
		)
	)
	users = list({user for user in users if user and user != "Guest"})
	subject = _("Certification {0}: {1}").format(label, cert.course)
	description = _(
		"{0}'s certification for {1} expires on {2}. Days remaining: {3}."
	).format(cert.employee_name or cert.employee, cert.course, cert.expiry_date, max(days, 0))
	if users:
		enqueue_create_notification(
			users,
			{
				"type": "Alert",
				"subject": subject,
				"email_content": description,
				"document_type": "QD Training Certification",
				"document_name": cert.name,
				"from_user": "Administrator",
			},
			dedupe_on=["subject", "document_type", "document_name"],
		)
		email_users = [user for user in users if "@" in user]
		if email_users:
			frappe.sendmail(recipients=email_users, subject=subject, message=description)


def training_request_query(user):
	return _employee_field_query("QD Training Request", "employee", user)


def training_nomination_query(user):
	return _employee_field_query("QD Training Nomination", "employee", user)


def training_enrollment_query(user):
	return _employee_field_query("QD Training Enrollment", "employee", user)


def training_attendance_query(user):
	return _employee_field_query("QD Training Attendance", "employee", user)


def training_assessment_query(user):
	return _employee_field_query("QD Training Assessment", "employee", user)


def training_certification_query(user):
	return _employee_field_query("QD Training Certification", "employee", user)


def _employee_field_query(doctype, fieldname, user):
	from qd_hrms.self_service import get_session_employee, is_privileged

	if is_privileged(user):
		return ""
	employee = get_session_employee(user)
	if not employee:
		return "1=0"
	return f"`tab{doctype}`.`{fieldname}` = {frappe.db.escape(employee)}"


def has_training_record_permission(doc, ptype=None, user=None, debug=False):
	from qd_hrms.self_service import get_session_employee, is_privileged

	user = user or frappe.session.user
	if is_privileged(user):
		return None
	return doc.get("employee") == get_session_employee(user)
