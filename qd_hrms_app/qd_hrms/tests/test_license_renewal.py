from unittest import TestCase

from qd_hrms.licenses import license_status


class TestLicenseRenewal(TestCase):
	def test_active_outside_lead_window(self):
		self.assertEqual(license_status(90, 30), "Active")

	def test_due_when_inside_lead_window(self):
		self.assertEqual(license_status(30, 30), "Due for Renewal")
		self.assertEqual(license_status(7, 30), "Due for Renewal")

	def test_expired_beats_open_renewal(self):
		self.assertEqual(license_status(-1, 30, has_open_renewal=True), "Expired")

	def test_open_renewal_marks_in_progress(self):
		self.assertEqual(license_status(10, 30, has_open_renewal=True), "Renewal In Progress")

	def test_terminal_statuses_are_sticky(self):
		self.assertEqual(license_status(-10, 30, current="Revoked"), "Revoked")
		self.assertEqual(license_status(5, 30, current="Renewed"), "Renewed")
