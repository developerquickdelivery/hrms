"""Customize standard HRMS Job Offer for Quick Delivery offer letters."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from qd_hrms.job_offer import STANDARD_TEMPLATE

PRINT_FORMAT = "QD Standard Offer Letter"

DEFAULT_BENEFITS = """<ul>
<li>Statutory pension and benefits in accordance with Ethiopian law.</li>
<li>Paid leave and public holidays in accordance with company policy.</li>
<li>Other role-specific benefits approved by Quick Delivery.</li>
</ul>"""

DEFAULT_CONDITIONS = """<ul>
<li>Satisfactory verification of identity, qualifications, and references.</li>
<li>Compliance with Quick Delivery policies, confidentiality, and code of conduct.</li>
<li>Successful completion of the stated probation period.</li>
</ul>"""

OFFER_TERMS = (
	"Position",
	"Grade",
	"Salary",
	"Benefits",
	"Start Date",
	"Probation",
	"Conditions",
)

PRINT_HTML = """
<style>
	.qd-offer { font-family: Inter, Arial, sans-serif; color: #1e293b; font-size: 12px; line-height: 1.6; }
	.qd-offer h1 { color: #0c499c; font-size: 24px; margin: 0 0 4px; }
	.qd-offer .subtitle { color: #64748b; margin-bottom: 24px; }
	.qd-offer .meta { width: 100%; margin: 18px 0 22px; border-collapse: collapse; }
	.qd-offer .meta td { padding: 8px 10px; border: 1px solid #e2e8f0; vertical-align: top; }
	.qd-offer .meta td:first-child { width: 30%; color: #0c499c; font-weight: 600; background: #f8fafc; }
	.qd-offer h2 { color: #0c499c; font-size: 15px; border-bottom: 2px solid #f67a0d; padding-bottom: 4px; margin-top: 22px; }
	.qd-offer .signature { margin-top: 42px; width: 100%; }
	.qd-offer .signature td { width: 50%; padding-right: 40px; vertical-align: bottom; }
	.qd-offer .line { border-top: 1px solid #334155; margin-top: 52px; padding-top: 5px; }
</style>

<div class="qd-offer">
	<h1>Offer of Employment</h1>
	<div class="subtitle">{{ doc.company }} · {{ frappe.utils.formatdate(doc.offer_date) }}</div>

	<p>Dear <strong>{{ doc.applicant_name }}</strong>,</p>
	<p>
		We are pleased to offer you employment with <strong>{{ doc.company }}</strong>.
		The principal terms of this offer are set out below.
	</p>

	<table class="meta">
		<tr><td>Position</td><td>{{ doc.custom_qd_position or doc.designation }}</td></tr>
		<tr><td>Designation</td><td>{{ doc.designation }}</td></tr>
		<tr><td>Grade</td><td>{{ doc.custom_qd_employee_grade }}</td></tr>
		<tr>
			<td>Monthly Base Salary</td>
			<td>{{ frappe.utils.fmt_money(doc.custom_qd_base_salary, currency=doc.custom_qd_salary_currency) }}</td>
		</tr>
		<tr><td>Start Date</td><td>{{ frappe.utils.formatdate(doc.custom_qd_start_date) }}</td></tr>
		<tr>
			<td>Probation</td>
			<td>
				{{ doc.custom_qd_probation_months }} month(s)
				{% if doc.custom_qd_probation_end_date %}
					— through {{ frappe.utils.formatdate(doc.custom_qd_probation_end_date) }}
				{% endif %}
			</td>
		</tr>
	</table>

	<h2>Benefits</h2>
	<div>{{ doc.custom_qd_benefits or "" }}</div>

	<h2>Conditions of Offer</h2>
	<div>{{ doc.custom_qd_conditions or "" }}</div>

	{% if doc.terms %}
		<h2>Additional Terms and Conditions</h2>
		<div>{{ doc.terms }}</div>
	{% endif %}

	<p>
		Please confirm your acceptance by signing below. We look forward to welcoming you to
		{{ doc.company }}.
	</p>

	<table class="signature">
		<tr>
			<td><div class="line">Authorized Signatory<br>{{ doc.company }}</div></td>
			<td><div class="line">{{ doc.applicant_name }}<br>Date</div></td>
		</tr>
	</table>
</div>
"""


def run():
	ensure_custom_fields()
	ensure_offer_term_template()
	ensure_print_format()
	frappe.clear_cache(doctype="Job Offer")
	return {
		"doctype": "Job Offer",
		"term_template": STANDARD_TEMPLATE,
		"print_format": PRINT_FORMAT,
		"fields": [
			"custom_qd_position",
			"custom_qd_employee_grade",
			"custom_qd_base_salary",
			"custom_qd_benefits",
			"custom_qd_start_date",
			"custom_qd_probation_months",
			"custom_qd_probation_end_date",
			"custom_qd_conditions",
		],
	}


def ensure_custom_fields():
	create_custom_fields(
		{
			"Job Offer": [
				{
					"fieldname": "custom_qd_offer_details",
					"fieldtype": "Section Break",
					"label": "Offer Details",
					"insert_after": "company",
				},
				{
					"fieldname": "custom_qd_position",
					"fieldtype": "Link",
					"label": "Position",
					"options": "QD Position",
					"insert_after": "custom_qd_offer_details",
					"reqd": 1,
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_employee_grade",
					"fieldtype": "Link",
					"label": "Employee Grade",
					"options": "Employee Grade",
					"insert_after": "custom_qd_position",
					"reqd": 1,
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "custom_qd_offer_column",
					"fieldtype": "Column Break",
					"insert_after": "custom_qd_employee_grade",
				},
				{
					"fieldname": "custom_qd_salary_currency",
					"fieldtype": "Link",
					"label": "Salary Currency",
					"options": "Currency",
					"insert_after": "custom_qd_offer_column",
					"reqd": 1,
				},
				{
					"fieldname": "custom_qd_base_salary",
					"fieldtype": "Currency",
					"label": "Monthly Base Salary",
					"options": "custom_qd_salary_currency",
					"insert_after": "custom_qd_salary_currency",
					"reqd": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "custom_qd_start_probation",
					"fieldtype": "Section Break",
					"label": "Start and Probation",
					"insert_after": "custom_qd_base_salary",
				},
				{
					"fieldname": "custom_qd_start_date",
					"fieldtype": "Date",
					"label": "Start Date",
					"insert_after": "custom_qd_start_probation",
					"reqd": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "custom_qd_probation_months",
					"fieldtype": "Int",
					"label": "Probation Period (Months)",
					"insert_after": "custom_qd_start_date",
					"default": "3",
					"reqd": 1,
				},
				{
					"fieldname": "custom_qd_probation_column",
					"fieldtype": "Column Break",
					"insert_after": "custom_qd_probation_months",
				},
				{
					"fieldname": "custom_qd_probation_end_date",
					"fieldtype": "Date",
					"label": "Probation End Date",
					"insert_after": "custom_qd_probation_column",
					"read_only": 1,
				},
				{
					"fieldname": "custom_qd_terms_section",
					"fieldtype": "Section Break",
					"label": "Benefits and Conditions",
					"insert_after": "custom_qd_probation_end_date",
				},
				{
					"fieldname": "custom_qd_benefits",
					"fieldtype": "Text Editor",
					"label": "Benefits",
					"insert_after": "custom_qd_terms_section",
					"default": DEFAULT_BENEFITS,
					"reqd": 1,
				},
				{
					"fieldname": "custom_qd_conditions",
					"fieldtype": "Text Editor",
					"label": "Conditions",
					"insert_after": "custom_qd_benefits",
					"default": DEFAULT_CONDITIONS,
					"reqd": 1,
				},
			]
		},
		ignore_validate=True,
		update=True,
	)


def ensure_offer_term_template():
	for term in OFFER_TERMS:
		if not frappe.db.exists("Offer Term", term):
			frappe.get_doc({"doctype": "Offer Term", "offer_term": term}).insert(
				ignore_permissions=True
			)

	if frappe.db.exists("Job Offer Term Template", STANDARD_TEMPLATE):
		doc = frappe.get_doc("Job Offer Term Template", STANDARD_TEMPLATE)
		doc.set("offer_terms", [])
	else:
		doc = frappe.new_doc("Job Offer Term Template")
		doc.title = STANDARD_TEMPLATE

	for term in OFFER_TERMS:
		doc.append("offer_terms", {"offer_term": term, "value": "Set from offer details"})
	doc.save(ignore_permissions=True)


def ensure_print_format():
	if frappe.db.exists("Print Format", PRINT_FORMAT):
		doc = frappe.get_doc("Print Format", PRINT_FORMAT)
	else:
		doc = frappe.new_doc("Print Format")
		doc.name = PRINT_FORMAT

	doc.doc_type = "Job Offer"
	doc.module = "QD HRMS"
	doc.standard = "No"
	doc.custom_format = 1
	doc.print_format_type = "Jinja"
	doc.print_format_builder = 0
	doc.line_breaks = 0
	doc.show_section_headings = 0
	doc.disabled = 0
	doc.html = PRINT_HTML
	doc.save(ignore_permissions=True)

	frappe.db.delete(
		"Property Setter",
		{"doc_type": "Job Offer", "property": "default_print_format"},
	)
	make_property_setter(
		"Job Offer",
		None,
		"default_print_format",
		PRINT_FORMAT,
		"Data",
		validate_fields_for_doctype=False,
		is_system_generated=False,
	)
