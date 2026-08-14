#!/usr/bin/env python3
"""On-prem biometric listener: pull ZKTeco (or similar) logs and POST to Frappe.

Run this on a machine that can reach the fingerprint devices (often a hub PC),
not necessarily the Frappe server.

Config file (JSON), default ./qd_biometric_listener.json:

{
  "frappe_url": "http://127.0.0.1:8000",
  "poll_seconds": 15,
  "devices": [
    {
      "device_id": "HUB-01",
      "vendor": "ZKTeco",
      "ip": "192.168.1.201",
      "port": 4370,
      "secret": "paste-api-secret-from-QD-Biometric-Device"
    }
  ]
}

ZKTeco pull needs: pip install pyzk
Generic HTTP devices should POST directly to Frappe; this process is for TCP pull.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("qd_biometric_listener.json")


def load_config() -> dict:
	if not CONFIG_PATH.exists():
		raise SystemExit(f"Missing config {CONFIG_PATH}. Copy the example from the module docstring.")
	return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def post_punches(url: str, device_id: str, secret: str, punches: list) -> dict:
	endpoint = url.rstrip("/") + "/api/method/qd_hrms.api.biometric.push_punches"
	body = json.dumps({"device_id": device_id, "punches": punches}).encode("utf-8")
	req = urllib.request.Request(
		endpoint,
		data=body,
		headers={
			"Content-Type": "application/json",
			"X-QD-Device-Secret": secret,
		},
		method="POST",
	)
	with urllib.request.urlopen(req, timeout=30) as resp:
		return json.loads(resp.read().decode("utf-8"))


def pull_zk(ip: str, port: int, since: datetime | None) -> list:
	from zk import ZK

	conn = None
	punches = []
	try:
		zk = ZK(ip, port=port, timeout=8, ommit_ping=True)
		conn = zk.connect()
		for row in conn.get_attendance() or []:
			stamp = getattr(row, "timestamp", None)
			if since and stamp and stamp <= since:
				continue
			punches.append(
				{
					"device_user_id": str(getattr(row, "user_id", "")),
					"timestamp": stamp.isoformat(sep=" ") if hasattr(stamp, "isoformat") else str(stamp),
					"log_type": getattr(row, "punch", None),
				}
			)
	finally:
		if conn:
			try:
				conn.disconnect()
			except Exception:
				pass
	return punches


def main():
	cfg = load_config()
	url = cfg.get("frappe_url") or "http://127.0.0.1:8000"
	wait = int(cfg.get("poll_seconds") or 15)
	state = {}
	print(f"QD biometric listener → {url} every {wait}s", flush=True)
	while True:
		for device in cfg.get("devices") or []:
			device_id = device.get("device_id")
			secret = device.get("secret")
			vendor = (device.get("vendor") or "ZKTeco").lower()
			try:
				if "http" in vendor:
					continue
				since = state.get(device_id)
				punches = pull_zk(device.get("ip"), int(device.get("port") or 4370), since)
				if not punches:
					continue
				result = post_punches(url, device_id, secret, punches)
				state[device_id] = datetime.now()
				print(f"{device_id}: {result.get('message') or result}", flush=True)
			except Exception as exc:
				print(f"{device_id}: {exc}", flush=True)
		time.sleep(wait)


if __name__ == "__main__":
	main()
