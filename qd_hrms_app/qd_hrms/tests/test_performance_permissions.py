from types import SimpleNamespace
from unittest import TestCase

import frappe

from qd_hrms.performance_permissions import (
	has_recognition_permission,
	pip_query,
	recognition_query,
)


class TestPerformancePermissions(TestCase):
	def test_guest_pip_query_is_denied(self):
		self.assertEqual(pip_query("Guest"), "1=0")

	def test_guest_recognition_query_is_denied(self):
		self.assertEqual(recognition_query("Guest"), "1=0")

	def test_private_recognition_hidden_from_other_employee(self):
		original = frappe.session.user
		try:
			frappe.set_user("guest@example.com")
			doc = SimpleNamespace(
				employee="EMP-002",
				visibility="Private",
				docstatus=1,
				owner="other@example.com",
				recognized_by="manager@example.com",
			)
			self.assertFalse(has_recognition_permission(doc, ptype="read"))
		finally:
			frappe.set_user(original)
