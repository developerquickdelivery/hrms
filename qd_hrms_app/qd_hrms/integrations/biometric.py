"""Create Employee Checkin from a biometric device pull (optional bench-side poll)."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime


def on_checkin(doc, method=None):
	if doc.meta.has_field("custom_qd_source") and not doc.custom_qd_source:
		doc.db_set("custom_qd_source", "Web", update_modified=False)


def poll_active_devices():
	"""Scheduler entry: only devices with poll_via_scheduler and a reachable IP."""
	devices = frappe.get_all(
		"QD Biometric Device",
		filters={"is_active": 1, "poll_via_scheduler": 1},
		pluck="name",
	)
	for name in devices:
		try:
			_poll_one(name)
		except Exception:
			frappe.log_error(title=f"QD biometric poll {name}")


def _poll_one(device_name: str):
	device = frappe.get_doc("QD Biometric Device", device_name)
	if not device.ip_address:
		return
	punches = _pull_zk(device)
	if punches is None:
		return
	from qd_hrms.api.biometric import ingest_punches

	secret = device.get_password("api_secret")
	ingest_punches(device.name, punches, secret)


def _pull_zk(device) -> list | None:
	try:
		from zk import ZK
	except ImportError:
		frappe.log_error(
			title="QD biometric: pyzk missing",
			message="Install pyzk on the listener host, or run scripts/qd_biometric_listener.py near the device.",
		)
		return None

	conn = None
	try:
		zk = ZK(device.ip_address, port=int(device.port or 4370), timeout=8, ommit_ping=True)
		conn = zk.connect()
		rows = conn.get_attendance() or []
		since = device.last_punch_time
		punches = []
		for row in rows:
			stamp = getattr(row, "timestamp", None)
			if since and stamp and stamp <= since:
				continue
			punches.append(
				{
					"device_user_id": str(getattr(row, "user_id", "")),
					"timestamp": str(stamp),
					"log_type": getattr(row, "punch", None),
				}
			)
		return punches
	finally:
		if conn:
			try:
				conn.disconnect()
			except Exception:
				pass
		device.db_set("last_sync", now_datetime(), update_modified=False)
