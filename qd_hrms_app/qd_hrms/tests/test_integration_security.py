from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from qd_hrms.integrations.runtime import (
	_endpoint,
	_get_oauth_token,
	_validate_outbound_url,
)


class TestIntegrationSecurity(TestCase):
	def setUp(self):
		self.integration = SimpleNamespace(
			base_url="https://api.example.com/v1/",
			client_id="client-id",
			oauth_token_url="https://auth.example.com/token",
			timeout_seconds=10,
			verify_ssl=True,
			get_password=lambda _fieldname: "client-secret",
		)

	def test_relative_path_stays_on_configured_host(self):
		self.assertEqual(
			_endpoint(self.integration, "employees"),
			"https://api.example.com/v1/employees",
		)

	def test_absolute_url_on_another_host_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			_validate_outbound_url(self.integration, "https://attacker.example/collect")

	@patch("qd_hrms.integrations.runtime.requests.post")
	def test_oauth_client_credentials_token(self, post):
		response = Mock()
		response.json.return_value = {"access_token": "access-token"}
		post.return_value = response

		self.assertEqual(_get_oauth_token(self.integration), "access-token")
		post.assert_called_once_with(
			"https://auth.example.com/token",
			data={"grant_type": "client_credentials"},
			auth=("client-id", "client-secret"),
			timeout=10,
			verify=True,
		)
		response.raise_for_status.assert_called_once_with()

	@patch("qd_hrms.integrations.runtime.requests.post")
	def test_oauth_response_requires_access_token(self, post):
		response = Mock()
		response.json.return_value = {}
		post.return_value = response

		with self.assertRaises(RuntimeError):
			_get_oauth_token(self.integration)
