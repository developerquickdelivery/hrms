import json
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document


class QDHRIntegration(Document):
	def validate(self):
		self._validate_json("configuration_json")
		self._validate_json("headers_json")
		self._validate_endpoint()
		self._validate_credentials()
		self._validate_retry()
		if not self.enabled:
			self.connection_status = "Disabled"
		elif self.connection_status == "Disabled":
			self.connection_status = "Not Configured"

	def after_insert(self):
		from qd_hrms.integrations.runtime import create_audit

		create_audit(self.name, "Configuration Created", status_to=self.connection_status)

	def on_update(self):
		if not self.get_doc_before_save():
			return
		from qd_hrms.integrations.runtime import create_audit

		if self.has_value_changed("enabled"):
			create_audit(
				self.name,
				"Enabled" if self.enabled else "Disabled",
				details=_("Integration enabled state changed."),
			)
		else:
			create_audit(
				self.name,
				"Configuration Updated",
				details=_("Integration configuration was updated."),
			)

	def _validate_json(self, fieldname):
		value = self.get(fieldname) or "{}"
		try:
			parsed = json.loads(value)
		except (TypeError, ValueError):
			frappe.throw(_("{0} must contain valid JSON.").format(self.meta.get_label(fieldname)))
		if not isinstance(parsed, dict):
			frappe.throw(_("{0} must be a JSON object.").format(self.meta.get_label(fieldname)))

	def _validate_endpoint(self):
		for fieldname in ("base_url", "oauth_token_url"):
			value = self.get(fieldname)
			if not value:
				continue
			parsed = urlparse(value)
			if parsed.scheme not in ("http", "https") or not parsed.netloc:
				frappe.throw(_("{0} must be an absolute HTTP or HTTPS URL.").format(
					self.meta.get_label(fieldname)
				))

	def _validate_credentials(self):
		required = {
			"Basic": ("username", "password"),
			"Bearer Token": ("bearer_token",),
			"API Key": ("api_key_header", "api_key"),
			"OAuth2": ("client_id", "client_secret", "oauth_token_url"),
			"SSO": ("client_id", "client_secret"),
		}
		if not self.enabled:
			return
		for fieldname in required.get(self.auth_type, ()):
			if not self.get(fieldname):
				frappe.throw(_("{0} is required for {1} authentication.").format(
					self.meta.get_label(fieldname), self.auth_type
				))
		if self.auth_type == "ERPNext Managed" and not (
			self.managed_reference_name
			or self.integration_type in ("Biometrics", "Banks", "Accounting", "SMS")
		):
			frappe.throw(_("Select a managed ERPNext configuration for this integration."))

	def _validate_retry(self):
		if self.max_retries < 0:
			frappe.throw(_("Maximum Retries cannot be negative."))
		if self.retry_delay_seconds < 0:
			frappe.throw(_("Retry Delay cannot be negative."))
		if self.backoff_multiplier < 1:
			frappe.throw(_("Backoff Multiplier must be at least 1."))
