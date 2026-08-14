"""Biometric punch API: hardware / listener → Employee Checkin."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def ignore_csrf_for_biometric():
	req = getattr(frappe.local, "request", None)
	if not req:
		return
	path = (req.path or "").rstrip("/")
	if path.endswith("/qd_hrms.api.biometric.push_punches"):
		frappe.flags.ignore_csrf = True


def _request_secret() -> str:
	req = getattr(frappe.local, "request", None)
	if req:
		secret = req.headers.get("X-QD-Device-Secret") or req.headers.get("X-QD-API-Key")
		if secret:
			return secret
	return frappe.form_dict.get("secret") or ""


def _load_device(device_id: str):
	if not device_id or not frappe.db.exists("QD Biometric Device", device_id):
		frappe.throw(_("Unknown biometric device."), frappe.AuthenticationError)
	device = frappe.get_doc("QD Biometric Device", device_id)
	if not device.is_active:
		frappe.throw(_("Device {0} is inactive.").format(device_id), frappe.AuthenticationError)
	return device


def _assert_secret(device, secret: str):
	expected = device.get_password("api_secret") if device.api_secret else None
	if not expected or not secret or secret != expected:
		frappe.throw(_("Invalid device secret."), frappe.AuthenticationError)


def _normalize_log_type(value) -> str | None:
	if value in (None, ""):
		return None
	text = str(value).strip().upper()
	if text in ("0", "IN", "CHECKIN", "CHECK-IN"):
		return "IN"
	if text in ("1", "OUT", "CHECKOUT", "CHECK-OUT"):
		return "OUT"
	return None


def _employee_for_device_user(device_user_id: str) -> str | None:
	if not device_user_id:
		return None
	return frappe.db.get_value("Employee", {"attendance_device_id": str(device_user_id).strip()}, "name")


def _already_logged(employee: str, stamp) -> bool:
	return bool(
		frappe.db.exists(
			"Employee Checkin",
			{"employee": employee, "time": stamp},
		)
	)


def _create_checkin(employee: str, stamp, log_type: str | None, device_id: str) -> str | None:
	if _already_logged(employee, stamp):
		return None
	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee
	doc.time = stamp
	if log_type:
		doc.log_type = log_type
	doc.device_id = device_id
	if doc.meta.has_field("custom_qd_source"):
		doc.custom_qd_source = "Biometric"
	if doc.meta.has_field("custom_qd_biometric_device"):
		doc.custom_qd_biometric_device = device_id
	doc.insert(ignore_permissions=True)
	return doc.name


def ingest_punches(device_id: str, punches: list, secret: str) -> dict:
	frappe.flags.ignore_permissions = True
	device = _load_device(device_id)
	_assert_secret(device, secret)
	try:
		return _ingest(device, punches)
	finally:
		frappe.flags.ignore_permissions = False


def _ingest(device, punches: list) -> dict:
	created = 0
	skipped = 0
	errors = []
	last_punch = None

	for raw in punches or []:
		user_id = raw.get("device_user_id") or raw.get("user_id") or raw.get("pin")
		stamp = raw.get("timestamp") or raw.get("time")
		log_type = _normalize_log_type(raw.get("log_type") or raw.get("punch"))
		if not user_id or not stamp:
			skipped += 1
			continue
		try:
			stamp = get_datetime(stamp)
		except Exception:
			skipped += 1
			errors.append(f"Bad timestamp for user {user_id}")
			continue
		employee = _employee_for_device_user(user_id)
		if not employee:
			skipped += 1
			errors.append(f"No Employee with Attendance Device ID {user_id}")
			continue
		name = _create_checkin(employee, stamp, log_type, device.name)
		if name:
			created += 1
			last_punch = stamp
		else:
			skipped += 1

	device.db_set("last_sync", now_datetime(), update_modified=False)
	if last_punch:
		device.db_set("last_punch_time", last_punch, update_modified=False)

	status = "Success"
	if errors and created:
		status = "Partial"
	elif not created and errors:
		status = "Failed"

	log = frappe.get_doc(
		{
			"doctype": "QD Biometric Sync Log",
			"biometric_device": device.name,
			"status": status,
			"started_on": now_datetime(),
			"finished_on": now_datetime(),
			"punches_received": len(punches or []),
			"punches_created": created,
			"punches_skipped": skipped,
			"message": "\n".join(errors[:20]),
			"raw_payload": json.dumps(punches[:50] if punches else [], default=str),
		}
	)
	log.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"device": device.name,
		"status": status,
		"created": created,
		"skipped": skipped,
		"errors": errors[:20],
	}


@frappe.whitelist(allow_guest=True)
def push_punches(device_id=None, punches=None, secret=None):
	"""Listener / device webhook. Header X-QD-Device-Secret or form secret."""
	device_id = device_id or frappe.form_dict.get("device_id")
	secret = secret or _request_secret()
	if isinstance(punches, str):
		punches = json.loads(punches)
	if punches is None and frappe.form_dict.get("punches"):
		raw = frappe.form_dict.get("punches")
		punches = json.loads(raw) if isinstance(raw, str) else raw
	if not punches and frappe.request and frappe.request.is_json:
		body = frappe.request.get_json(silent=True) or {}
		device_id = device_id or body.get("device_id")
		punches = body.get("punches") or body.get("logs")
		secret = secret or body.get("secret")
	if not device_id:
		frappe.throw(_("device_id is required."))
	if not isinstance(punches, list):
		frappe.throw(_("punches must be a list."))
	return ingest_punches(device_id, punches, secret)


@frappe.whitelist()
def list_devices():
	"""For the listener service (authenticated Frappe user / API key)."""
	rows = frappe.get_all(
		"QD Biometric Device",
		filters={"is_active": 1},
		fields=[
			"name",
			"device_id",
			"device_name",
			"vendor",
			"ip_address",
			"port",
			"poll_interval_sec",
			"last_punch_time",
		],
	)
	return rows
