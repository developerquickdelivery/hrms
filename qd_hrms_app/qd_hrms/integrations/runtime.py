"""Runtime for configured HR integrations.

Credentials remain on QD HR Integration Password fields. Logs only receive
sanitized headers, payloads, responses, and errors.
"""

from __future__ import annotations

import json
import time
import traceback
import uuid
from urllib.parse import urljoin, urlparse

import frappe
import requests
from frappe import _
from frappe.utils import add_to_date, now, now_datetime

SENSITIVE_KEYS = (
	"authorization",
	"password",
	"passwd",
	"secret",
	"token",
	"api_key",
	"apikey",
	"client_secret",
)


@frappe.whitelist()
def test_connection(integration):
	doc = frappe.get_doc("QD HR Integration", integration)
	doc.check_permission("write")
	if not doc.enabled:
		frappe.throw(_("Enable the integration before testing the connection."))

	if doc.auth_type == "ERPNext Managed" or doc.integration_type in (
		"Email",
		"SMS",
		"Biometrics",
		"Banks",
		"Accounting",
	):
		ok, message = _test_managed(doc)
		_update_connection(doc, ok, message)
		create_audit(
			doc.name,
			"Connection Test",
			status_to="Connected" if ok else "Failed",
			details=message,
		)
		return {"connected": ok, "message": message}

	if not doc.base_url:
		frappe.throw(_("Base URL is required for this integration type."))
	log = _create_log(
		doc,
		operation="Connection Test",
		method="GET",
		endpoint=urljoin(doc.base_url.rstrip("/") + "/", (doc.health_check_path or "/").lstrip("/")),
		payload=None,
		headers=None,
	)
	result = _perform(log.name)
	create_audit(
		doc.name,
		"Connection Test",
		status_to="Connected" if result.get("status") == "Success" else "Failed",
		integration_log=log.name,
		details=result.get("error_message") or _("Connection successful."),
	)
	return {
		"connected": result.get("status") == "Success",
		"message": result.get("error_message") or _("Connection successful."),
		"log": log.name,
	}


@frappe.whitelist()
def queue_request(
	integration,
	method="POST",
	path=None,
	payload=None,
	headers=None,
	operation="API Request",
):
	doc = frappe.get_doc("QD HR Integration", integration)
	doc.check_permission("write")
	if not doc.enabled:
		frappe.throw(_("Integration {0} is disabled.").format(doc.name))
	payload = _as_json_value(payload)
	headers = _as_json_value(headers) or {}
	endpoint = _endpoint(doc, path)
	log = _create_log(doc, operation, method, endpoint, payload, headers)
	create_audit(
		doc.name,
		"Request Queued",
		integration_log=log.name,
		details=f"{method.upper()} {endpoint}",
	)
	frappe.enqueue(
		"qd_hrms.integrations.runtime.process_log",
		queue="short",
		enqueue_after_commit=True,
		log_name=log.name,
	)
	return log.name


def process_log(log_name):
	return _perform(log_name)


def retry_failed_requests():
	logs = frappe.get_all(
		"QD HR Integration Log",
		filters={
			"status": "Retry Pending",
			"next_retry_on": ("<=", now_datetime()),
		},
		pluck="name",
		limit_page_length=100,
	)
	cache = frappe.cache()
	for name in logs:
		lock_key = f"qd_hrms:integration-retry:{name}"
		if not cache.set(lock_key, 1, nx=True, ex=300):
			continue
		try:
			if not _claim_retry_log(name):
				continue
			create_audit(
				frappe.db.get_value("QD HR Integration Log", name, "integration"),
				"Retry Executed",
				integration_log=name,
			)
			_perform(name)
		except Exception:
			frappe.log_error(
				title=f"HR integration retry failed: {name}",
				message=frappe.get_traceback(),
			)
		finally:
			cache.delete_value(lock_key)


def _claim_retry_log(name):
	current = frappe.db.get_value("QD HR Integration Log", name, "status")
	return current == "Retry Pending"


def _perform(log_name):
	log = frappe.get_doc("QD HR Integration Log", log_name)
	integration = frappe.get_doc("QD HR Integration", log.integration)
	if not integration.enabled:
		_finish_failed(log, integration, RuntimeError("Integration is disabled."))
		return log.as_dict()

	attempt = int(log.attempt_count or 0) + 1
	started = now_datetime()
	frappe.db.set_value(
		"QD HR Integration Log",
		log.name,
		{
			"status": "In Progress",
			"attempt_count": attempt,
			"started_on": started,
			"next_retry_on": None,
			"error_type": None,
			"error_message": None,
			"error_traceback": None,
		},
		update_modified=False,
	)
	start = time.monotonic()
	try:
		_validate_outbound_url(integration, log.endpoint)
		headers = _build_headers(integration, _as_json_value(log.request_headers) or {})
		payload = _as_json_value(log.request_payload)
		auth = _build_auth(integration)
		response = requests.request(
			method=log.request_method,
			url=log.endpoint,
			headers=headers,
			json=payload if payload is not None else None,
			auth=auth,
			timeout=int(integration.timeout_seconds or 30),
			verify=bool(integration.verify_ssl),
		)
		response.raise_for_status()
		duration = int((time.monotonic() - start) * 1000)
		body = _sanitize_response(response, integration)
		frappe.db.set_value(
			"QD HR Integration Log",
			log.name,
			{
				"status": "Success",
				"response_status": response.status_code,
				"response_body": body,
				"completed_on": now_datetime(),
				"duration_ms": duration,
			},
			update_modified=False,
		)
		_update_connection(integration, True, None)
		create_audit(
			integration.name,
			"Request Success",
			integration_log=log.name,
			status_to="Success",
		)
	except Exception as exc:
		_finish_failed(log, integration, exc, int((time.monotonic() - start) * 1000))
	return frappe.get_doc("QD HR Integration Log", log.name).as_dict()


def _finish_failed(log, integration, exc, duration_ms=0):
	attempt = int(
		frappe.db.get_value("QD HR Integration Log", log.name, "attempt_count") or 1
	)
	retry = bool(integration.retry_enabled) and attempt <= int(integration.max_retries or 0)
	status = "Retry Pending" if retry else "Abandoned"
	next_retry = None
	if retry:
		delay = int(integration.retry_delay_seconds or 0) * (
			float(integration.backoff_multiplier or 1) ** max(attempt - 1, 0)
		)
		next_retry = add_to_date(now_datetime(), seconds=int(delay), as_datetime=True)
	trace = _redact_text(traceback.format_exc(), integration)[:10000]
	frappe.db.set_value(
		"QD HR Integration Log",
		log.name,
		{
			"status": status,
			"completed_on": now_datetime(),
			"duration_ms": duration_ms,
			"next_retry_on": next_retry,
			"error_type": type(exc).__name__,
			"error_message": _redact_text(str(exc), integration)[:1000],
			"error_traceback": trace,
		},
		update_modified=False,
	)
	_update_connection(integration, False, str(exc))
	create_audit(
		integration.name,
		"Retry Scheduled" if retry else "Abandoned",
		integration_log=log.name,
		status_to=status,
		details=_redact_text(str(exc), integration)[:1000],
	)


def _create_log(integration, operation, method, endpoint, payload, headers):
	log = frappe.get_doc(
		{
			"doctype": "QD HR Integration Log",
			"integration": integration.name,
			"operation": operation,
			"direction": "Outbound",
			"correlation_id": str(uuid.uuid4()),
			"status": "Queued",
			"attempt_count": 0,
			"max_retries": integration.max_retries if integration.retry_enabled else 0,
			"request_method": method.upper(),
			"endpoint": endpoint,
			"request_headers": json.dumps(_sanitize(headers or {}), default=str, indent=2),
			"request_payload": json.dumps(_sanitize(payload), default=str, indent=2)
			if payload is not None
			else None,
		}
	)
	log.insert(ignore_permissions=True)
	return log


def _endpoint(integration, path):
	if path and str(path).startswith(("http://", "https://")):
		_validate_outbound_url(integration, str(path))
		return str(path)
	if not integration.base_url:
		frappe.throw(_("Base URL is required."))
	endpoint = urljoin(
		integration.base_url.rstrip("/") + "/",
		str(path or "").lstrip("/"),
	)
	_validate_outbound_url(integration, endpoint)
	return endpoint


def _validate_outbound_url(integration, endpoint):
	"""Prevent a request path from sending integration credentials to another host."""
	if not integration.base_url:
		frappe.throw(_("Base URL is required."))
	base = urlparse(integration.base_url)
	target = urlparse(endpoint)
	if target.scheme not in ("http", "https") or not target.netloc:
		frappe.throw(_("Integration endpoint must be an absolute HTTP or HTTPS URL."))
	if (target.scheme.lower(), target.hostname, target.port) != (
		base.scheme.lower(),
		base.hostname,
		base.port,
	):
		frappe.throw(_("Integration endpoint must use the configured Base URL host."))


def _build_headers(integration, stored_headers):
	headers = {}
	try:
		headers.update(json.loads(integration.headers_json or "{}"))
	except (TypeError, ValueError):
		pass
	headers.update(stored_headers or {})
	if integration.auth_type == "OAuth2":
		headers["Authorization"] = f"Bearer {_get_oauth_token(integration)}"
	elif integration.auth_type == "Bearer Token":
		headers["Authorization"] = f"Bearer {integration.get_password('bearer_token')}"
	elif integration.auth_type == "API Key":
		headers[integration.api_key_header or "X-API-Key"] = integration.get_password("api_key")
	return headers


def _get_oauth_token(integration):
	response = requests.post(
		integration.oauth_token_url,
		data={"grant_type": "client_credentials"},
		auth=(integration.client_id, integration.get_password("client_secret")),
		timeout=int(integration.timeout_seconds or 30),
		verify=bool(integration.verify_ssl),
	)
	response.raise_for_status()
	try:
		token = response.json().get("access_token")
	except (TypeError, ValueError):
		token = None
	if not token:
		raise RuntimeError(_("OAuth token response did not contain access_token."))
	return token


def _build_auth(integration):
	if integration.auth_type == "Basic":
		return (integration.username, integration.get_password("password"))
	return None


def _test_managed(doc):
	if doc.managed_reference_doctype and doc.managed_reference_name:
		exists = frappe.db.exists(doc.managed_reference_doctype, doc.managed_reference_name)
		return bool(exists), (
			_("Managed configuration is available.")
			if exists
			else _("Managed configuration does not exist.")
		)
	if doc.integration_type == "Email":
		ok = bool(frappe.db.exists("Email Account", {"enable_outgoing": 1}))
		return ok, _("Outgoing Email Account is configured.") if ok else _("No outgoing Email Account.")
	if doc.integration_type == "SMS":
		ok = bool(frappe.db.get_single_value("SMS Settings", "sms_gateway_url"))
		return ok, _("SMS gateway is configured.") if ok else _("SMS gateway is not configured.")
	if doc.integration_type == "Biometrics":
		ok = bool(
			frappe.db.exists("QD Biometric Device", {"is_active": 1})
			if frappe.db.exists("DocType", "QD Biometric Device")
			else False
		)
		return ok, _("Active biometric device found.") if ok else _("No active biometric device.")
	if doc.integration_type == "Banks":
		ok = bool(frappe.db.count("Bank Account"))
		return ok, _("Bank accounts are configured.") if ok else _("No bank accounts configured.")
	if doc.integration_type == "Accounting":
		ok = bool(frappe.db.count("Account"))
		return ok, _("Accounting chart is available.") if ok else _("No accounting chart available.")
	if doc.integration_type == "Document Storage" and not doc.base_url:
		return True, _("Local Frappe File storage is available.")
	return False, _("No managed connection test is available; configure a Base URL.")


def _update_connection(integration, success, error):
	failures = 0 if success else int(integration.consecutive_failures or 0) + 1
	status = "Connected" if success else ("Degraded" if failures < 3 else "Failed")
	values = {
		"connection_status": status,
		"last_checked_on": now_datetime(),
		"consecutive_failures": failures,
		"last_error": None if success else _redact_text(str(error), integration)[:1000],
	}
	if success:
		values["last_success_on"] = now_datetime()
	frappe.db.set_value("QD HR Integration", integration.name, values, update_modified=False)
	integration.connection_status = status
	integration.consecutive_failures = failures


def create_audit(
	integration,
	action,
	status_from=None,
	status_to=None,
	integration_log=None,
	details=None,
):
	if not frappe.db.exists("DocType", "QD HR Integration Audit"):
		return
	frappe.get_doc(
		{
			"doctype": "QD HR Integration Audit",
			"integration": integration,
			"action": action,
			"event_time": now(),
			"performed_by": frappe.session.user or "Administrator",
			"status_from": status_from,
			"status_to": status_to,
			"integration_log": integration_log,
			"details": details,
		}
	).insert(ignore_permissions=True)


def _as_json_value(value):
	if value in (None, ""):
		return None
	if isinstance(value, (dict, list)):
		return value
	try:
		return json.loads(value)
	except (TypeError, ValueError):
		return value


def _sanitize(value):
	if isinstance(value, dict):
		return {
			key: "***REDACTED***"
			if any(part in str(key).lower() for part in SENSITIVE_KEYS)
			else _sanitize(item)
			for key, item in value.items()
		}
	if isinstance(value, list):
		return [_sanitize(item) for item in value]
	return value


def _sanitize_response(response, integration):
	try:
		value = json.dumps(_sanitize(response.json()), default=str, indent=2)
	except (TypeError, ValueError):
		value = response.text
	return _redact_text(value, integration)[:10000]


def _redact_text(value, integration):
	text = value or ""
	for fieldname in ("password", "bearer_token", "api_key", "client_secret"):
		try:
			secret = integration.get_password(fieldname)
		except Exception:
			secret = None
		if secret:
			text = text.replace(secret, "***REDACTED***")
	return text
