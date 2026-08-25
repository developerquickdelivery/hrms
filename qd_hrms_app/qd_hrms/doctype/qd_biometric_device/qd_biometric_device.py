# Copyright (c) 2026, Quick Delivery Service

import frappe
from frappe.model.document import Document


class QDBiometricDevice(Document):
	def before_insert(self):
		if not self.api_secret:
			self.api_secret = frappe.generate_hash(length=32)

	def validate(self):
		if self.device_id:
			self.device_id = self.device_id.strip()
