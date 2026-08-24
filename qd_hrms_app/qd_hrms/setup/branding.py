"""Apply Quick Delivery branding to Website Settings, navbar, print, and email."""

from __future__ import annotations

APP_NAME = "Quick Delivery"
TAGLINE = "Fast, Reliable, Secure"
PRIMARY_BLUE = "#0C499C"
SECONDARY_ORANGE = "#F67A0D"

# Repo ships qd-favicon.png + qd-mark.svg; logo/splash files are optional.
FAVICON_URL = "/assets/qd_hrms/images/qd-favicon.png"
MARK_URL = "/assets/qd_hrms/images/qd-mark.svg"
LOGO_URL = FAVICON_URL
SPLASH_URL = FAVICON_URL


def run():
	import frappe

	_website_settings()
	_navbar_settings()
	_system_settings()
	_letter_head()
	_print_settings()
	_website_theme()
	frappe.clear_cache()
	return {
		"app_name": APP_NAME,
		"primary": PRIMARY_BLUE,
		"secondary": SECONDARY_ORANGE,
	}


def update_website_context(context):
	context.favicon = FAVICON_URL
	context.splash_image = SPLASH_URL
	context.app_name = APP_NAME
	context.brand_html = APP_NAME


def extend_bootinfo(bootinfo):
	bootinfo.sysdefaults = bootinfo.sysdefaults or {}
	bootinfo.app_name = APP_NAME
	bootinfo.app_logo_url = LOGO_URL


def _set(doc, field, value):
	if doc.meta.has_field(field):
		doc.set(field, value)


def _website_settings():
	import frappe

	ws = frappe.get_single("Website Settings")
	_set(ws, "app_name", APP_NAME)
	_set(ws, "app_logo", LOGO_URL)
	_set(ws, "favicon", FAVICON_URL)
	_set(ws, "splash_image", SPLASH_URL)
	_set(ws, "banner_image", SPLASH_URL)
	_set(
		ws,
		"brand_html",
		(
			f'<img src="{LOGO_URL}" alt="{APP_NAME}" '
			'style="height:36px;width:auto;max-width:120px;border-radius:6px;vertical-align:middle;">'
		),
	)
	_set(ws, "footer_powered", f"{APP_NAME} · {TAGLINE}")
	ws.flags.ignore_validate = True
	ws.save(ignore_permissions=True)
	frappe.db.commit()


def _navbar_settings():
	import frappe

	if not frappe.db.exists("DocType", "Navbar Settings"):
		return
	nav = frappe.get_single("Navbar Settings")
	_set(nav, "app_logo", LOGO_URL)
	nav.flags.ignore_validate = True
	nav.save(ignore_permissions=True)
	frappe.db.commit()


def _system_settings():
	import frappe

	ss = frappe.get_single("System Settings")
	if ss.meta.has_field("app_name"):
		ss.app_name = APP_NAME
		ss.flags.ignore_validate = True
		ss.save(ignore_permissions=True)
		frappe.db.commit()


def _letter_head():
	import frappe

	name = APP_NAME
	header = f"""
<div style="font-family:Inter,Arial,sans-serif;border-bottom:3px solid {SECONDARY_ORANGE};padding:8px 0 12px;margin-bottom:16px;">
	<table width="100%" cellpadding="0" cellspacing="0">
		<tr>
			<td style="width:72px;vertical-align:middle;">
				<img src="{SPLASH_URL}" alt="{APP_NAME}" style="height:56px;border-radius:8px;">
			</td>
			<td style="vertical-align:middle;padding-left:12px;">
				<div style="font-size:18px;font-weight:700;color:{PRIMARY_BLUE};letter-spacing:0.02em;">{APP_NAME.upper()}</div>
				<div style="font-size:11px;color:#64748b;letter-spacing:0.12em;text-transform:uppercase;">{TAGLINE}</div>
			</td>
		</tr>
	</table>
</div>
"""
	footer = f"""
<div style="font-family:Inter,Arial,sans-serif;border-top:2px solid {PRIMARY_BLUE};padding-top:10px;margin-top:24px;color:#64748b;font-size:11px;">
	<strong style="color:{PRIMARY_BLUE};">{APP_NAME}</strong>
	&nbsp;·&nbsp;{TAGLINE}
</div>
"""
	if frappe.db.exists("Letter Head", name):
		doc = frappe.get_doc("Letter Head", name)
	else:
		doc = frappe.new_doc("Letter Head")
		doc.letter_head_name = name
	doc.source = "HTML"
	doc.footer_source = "HTML"
	doc.content = header
	doc.footer = footer
	doc.is_default = 1
	doc.disabled = 0
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def _print_settings():
	import frappe

	if not frappe.db.exists("DocType", "Print Settings"):
		return
	ps = frappe.get_single("Print Settings")
	if ps.meta.has_field("with_letterhead"):
		ps.with_letterhead = 1
	if ps.meta.has_field("letter_head"):
		ps.letter_head = APP_NAME
	ps.flags.ignore_validate = True
	ps.save(ignore_permissions=True)
	frappe.db.commit()


def _website_theme():
	import frappe

	theme_name = "Quick Delivery"
	if not frappe.db.exists("DocType", "Website Theme"):
		return
	try:
		if frappe.db.exists("Website Theme", theme_name):
			theme = frappe.get_doc("Website Theme", theme_name)
		else:
			theme = frappe.new_doc("Website Theme")
			theme.theme = theme_name
			theme.module = "Website"
			theme.custom = 1
		if theme.meta.has_field("google_font"):
			theme.google_font = "Inter"
		if theme.meta.has_field("font_size"):
			theme.font_size = "15px"
		if theme.meta.has_field("primary_color"):
			theme.primary_color = PRIMARY_BLUE
		if theme.meta.has_field("text_color"):
			theme.text_color = "#1e293b"
		if theme.meta.has_field("background_color"):
			theme.background_color = "#ffffff"
		if theme.meta.has_field("button_rounded_corners"):
			theme.button_rounded_corners = 1
		theme.save(ignore_permissions=True)
		ws = frappe.get_single("Website Settings")
		if ws.meta.has_field("website_theme"):
			ws.website_theme = theme_name
			ws.flags.ignore_validate = True
			ws.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="QD branding website theme")
