"""Install / migrate hooks for qd_hrms."""

from __future__ import annotations

import frappe

def after_install():
	from qd_hrms.setup.branding import run as run_branding
	from qd_hrms.setup.people import run as run_people
	from qd_hrms.setup.requisition import run as run_requisition
	from qd_hrms.setup.onboarding import run as run_onboarding
	from qd_hrms.setup.attendance import run as run_attendance
	from qd_hrms.setup.leave import run as run_leave
	from qd_hrms.setup.leave_payroll import run as run_leave_payroll
	from qd_hrms.setup.learning import run as run_learning
	from qd_hrms.setup.licenses import run as run_licenses
	from qd_hrms.setup.employee_relations import run as run_employee_relations
	from qd_hrms.setup.employee_assets import run as run_employee_assets
	from qd_hrms.setup.employee_requests import run as run_employee_requests
	from qd_hrms.setup.separation import run as run_separation
	from qd_hrms.setup.analytics import run as run_analytics
	from qd_hrms.setup.notifications import run as run_notifications
	from qd_hrms.setup.integrations import run as run_integrations
	from qd_hrms.setup.hr_admin import run as run_hr_admin
	from qd_hrms.setup.organization import run as run_organization
	from qd_hrms.setup.job_grades import run as run_job_grades
	from qd_hrms.setup.positions import run as run_positions
	from qd_hrms.setup.org_data import run as run_org_data
	from qd_hrms.setup.employee_directory import run as run_employee_directory
	from qd_hrms.setup.employment_info import run as run_employment_info
	from qd_hrms.setup.bank_tax_pension import run as run_bank_tax_pension
	from qd_hrms.setup.promotion import run as run_promotion
	from qd_hrms.setup.offers import run as run_offers
	from qd_hrms.setup.performance import run as run_performance
	from qd_hrms.setup.self_service import run as run_self_service

	run_branding()
	run_people()
	run_organization()
	run_job_grades()
	run_positions()
	run_org_data()
	run_employee_directory()
	run_employment_info()
	run_bank_tax_pension()
	run_promotion()
	run_offers()
	run_requisition()
	run_onboarding()
	run_attendance()
	run_leave_payroll()
	run_leave()
	run_performance()
	run_learning()
	run_licenses()
	run_employee_relations()
	run_employee_assets()
	run_employee_requests()
	run_separation()
	run_analytics()
	run_notifications()
	run_integrations()
	run_hr_admin()
	run_self_service()


def after_migrate():
	"""Re-sync desk metadata only; do not rebuild workflows on every migrate."""
	from qd_hrms.setup.self_service import run as run_self_service
	from qd_hrms.setup.analytics import run as run_analytics
	from qd_hrms.setup.notifications import run as run_notifications
	from qd_hrms.setup.integrations import run as run_integrations
	from qd_hrms.setup.hr_admin import run as run_hr_admin

	run_self_service()
	run_analytics()
	run_notifications()
	run_integrations()
	run_hr_admin()
	frappe.clear_cache()
