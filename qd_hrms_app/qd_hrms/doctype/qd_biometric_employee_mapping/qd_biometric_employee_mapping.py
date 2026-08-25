import frappe
from frappe.model.document import Document


class QDBiometricEmployeeMapping(Document):
	def autoname(self):
		self.mapping_key = f"{self.biometric_device}::{str(self.device_user_id).strip()}"
		self.name = self.mapping_key

	def validate(self):
		self.device_user_id = str(self.device_user_id).strip()
		self.mapping_key = f"{self.biometric_device}::{self.device_user_id}"
		duplicate = frappe.db.exists(
			self.doctype,
			{
				"biometric_device": self.biometric_device,
				"device_user_id": self.device_user_id,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				f"Device user {self.device_user_id} is already mapped for {self.biometric_device}."
			)
