"""Install / migrate hooks for qd_hrms."""

from __future__ import annotations


def after_install():
	from qd_hrms.setup.branding import run as run_branding
	from qd_hrms.setup.people import run as run_people
	from qd_hrms.setup.requisition import run as run_requisition
	from qd_hrms.setup.onboarding import run as run_onboarding
	from qd_hrms.setup.attendance import run as run_attendance

	run_branding()
	run_people()
	run_requisition()
	run_onboarding()
	run_attendance()


def after_migrate():
	after_install()
