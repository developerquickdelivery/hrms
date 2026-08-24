"""Biometric punch API: hardware / listener → Employee Checkin."""

from __future__ import annotations

import json
import hmac
from hashlib import sha256

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
	if (
		not expected
		or not secret
		or not hmac.compare_digest(str(secret).encode(), str(expected).encode())
	):
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


def _mapping_for_device_user(device, device_user_id: str):
	device_user_id = str(device_user_id).strip()
	name = frappe.db.get_value(
		"QD Biometric Employee Mapping",
		{
			"biometric_device": device.name,
			"device_user_id": device_user_id,
			"is_active": 1,
		},
		"name",
	)
	if name:
		return frappe.get_doc("QD Biometric Employee Mapping", name)

	# Backward-compatible migration: convert the old global Employee device ID
	# into a durable device-scoped mapping on first use.
	employees = frappe.get_all(
		"Employee",
		filters={"attendance_device_id": device_user_id, "status": "Active"},
		pluck="name",
		limit=2,
	)
	if len(employees) != 1:
		return None
	return frappe.get_doc(
		{
			"doctype": "QD Biometric Employee Mapping",
			"biometric_device": device.name,
			"device_user_id": device_user_id,
			"employee": employees[0],
			"is_active": 1,
			"notes": "Migrated automatically from Employee Attendance Device ID.",
		}
	).insert(ignore_permissions=True)


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


def _event_key(device_name: str, user_id: str, stamp, log_type: str | None, raw: dict) -> str:
	source_id = raw.get("event_id") or raw.get("id") or raw.get("uid")
	identity = source_id or f"{user_id}|{stamp}|{log_type or ''}"
	return sha256(f"{device_name}|{identity}".encode()).hexdigest()


def _capture_raw(device, raw: dict):
	user_id = raw.get("device_user_id") or raw.get("user_id") or raw.get("pin")
	stamp = raw.get("timestamp") or raw.get("time")
	log_type = _normalize_log_type(raw.get("log_type") or raw.get("punch"))
	if not user_id or not stamp:
		return None, "Device User ID and timestamp are required"
	try:
		stamp = get_datetime(stamp)
	except Exception:
		return None, f"Bad timestamp for user {user_id}"

	key = _event_key(device.name, str(user_id).strip(), stamp, log_type, raw)
	existing = frappe.db.exists("QD Raw Checkin", key)
	if existing:
		return frappe.get_doc("QD Raw Checkin", existing), "Duplicate"

	doc = frappe.get_doc(
		{
			"doctype": "QD Raw Checkin",
			"event_key": key,
			"biometric_device": device.name,
			"connector": device.connector,
			"device_user_id": str(user_id).strip(),
			"timestamp": stamp,
			"log_type": log_type,
			"status": "Received",
			"raw_payload": json.dumps(raw, default=str, sort_keys=True),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc, None


def process_raw_checkin(raw_doc) -> tuple[str, str | None]:
	if isinstance(raw_doc, str):
		raw_doc = frappe.get_doc("QD Raw Checkin", raw_doc)
	if raw_doc.status == "Processed":
		return "Duplicate", raw_doc.employee_checkin

	device = frappe.get_doc("QD Biometric Device", raw_doc.biometric_device)
	mapping = _mapping_for_device_user(device, raw_doc.device_user_id)
	if not mapping:
		message = (
			f"No active mapping for device {device.name}, user {raw_doc.device_user_id}. "
			"Create QD Biometric Employee Mapping and reprocess."
		)
		frappe.db.set_value(
			"QD Raw Checkin",
			raw_doc.name,
			{"status": "Failed", "error_message": message},
			update_modified=False,
		)
		return "Failed", None

	frappe.db.set_value(
		"QD Raw Checkin",
		raw_doc.name,
		{
			"status": "Mapped",
			"employee_mapping": mapping.name,
			"employee": mapping.employee,
			"error_message": None,
		},
		update_modified=False,
	)
	try:
		checkin = _create_checkin(
			mapping.employee,
			raw_doc.timestamp,
			raw_doc.log_type,
			device.name,
		)
		if not checkin:
			checkin = frappe.db.get_value(
				"Employee Checkin",
				{"employee": mapping.employee, "time": raw_doc.timestamp},
				"name",
			)
		frappe.db.set_value(
			"QD Raw Checkin",
			raw_doc.name,
			{
				"status": "Processed",
				"employee_checkin": checkin,
				"processed_on": now_datetime(),
				"error_message": None,
			},
			update_modified=False,
		)
		return "Processed", checkin
	except Exception as exc:
		message = str(exc)
		status = "Blocked" if "Period Locked" in message or "period is locked" in message else "Failed"
		frappe.db.set_value(
			"QD Raw Checkin",
			raw_doc.name,
			{"status": status, "error_message": message[:500]},
			update_modified=False,
		)
		return status, None


def ingest_punches(device_id: str, punches: list, secret: str) -> dict:
	device = _load_device(device_id)
	_assert_secret(device, secret)
	previous_ignore_permissions = getattr(frappe.flags, "ignore_permissions", False)
	frappe.flags.ignore_permissions = True
	try:
		return _ingest(device, punches)
	finally:
		frappe.flags.ignore_permissions = previous_ignore_permissions


def _ingest(device, punches: list) -> dict:
	created = 0
	skipped = 0
	errors = []
	last_punch = None

	for raw in punches or []:
		raw_doc, capture_error = _capture_raw(device, raw)
		if not raw_doc:
			skipped += 1
			errors.append(capture_error)
			continue
		last_punch = max(last_punch, raw_doc.timestamp) if last_punch else raw_doc.timestamp
		if capture_error == "Duplicate":
			skipped += 1
			continue
		result, _checkin = process_raw_checkin(raw_doc)
		if result == "Processed":
			created += 1
		else:
			skipped += 1
			errors.append(f"{raw_doc.device_user_id}: {result}")

	device.db_set("last_sync", now_datetime(), update_modified=False)
	if last_punch:
		device.db_set("last_punch_time", last_punch, update_modified=False)
	if device.connector:
		frappe.db.set_value(
			"QD Biometric Connector",
			device.connector,
			{"last_heartbeat": now_datetime(), "status": "Active"},
			update_modified=False,
		)

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
	if len(punches) > 1000:
		frappe.throw(_("A maximum of 1,000 punches is allowed per request."))
	if any(not isinstance(punch, dict) for punch in punches):
		frappe.throw(_("Each punch must be a JSON object."))
	return ingest_punches(device_id, punches, secret)


@frappe.whitelist()
def list_devices():
	"""For the listener service (HR / integration operators only)."""
	if not set(frappe.get_roles()) & {"System Manager", "HR Manager", "HR User"}:
		frappe.throw(_("Not permitted to list biometric devices."), frappe.PermissionError)
	rows = frappe.get_all(
		"QD Biometric Device",
		filters={"is_active": 1},
		fields=[
			"name",
			"device_id",
			"device_name",
			"vendor",
			"connector",
			"ip_address",
			"port",
			"poll_interval_sec",
			"last_punch_time",
		],
	)
	return rows


@frappe.whitelist()
def reprocess_raw_checkin(name: str):
	allowed = {"System Manager", "HR Manager", "HR User"}
	if not (set(frappe.get_roles()) & allowed) and frappe.session.user != "Administrator":
		frappe.throw(_("Not permitted to reprocess biometric records."), frappe.PermissionError)
	result, checkin = process_raw_checkin(name)
	frappe.db.commit()
	return {"name": name, "status": result, "employee_checkin": checkin}
