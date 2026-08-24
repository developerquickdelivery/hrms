import os
import frappe

def apply_all():
    comp = frappe.get_all("Company", fields=["name", "abbr"])[0]
    C, A = comp.name, comp.abbr
    print(f"Target Company: {C} ({A})")

    # 1. Custom Fields
    print("Configuring custom fields...")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(
        {
            "Designation": [
                {
                    "fieldname": "custom_qd_is_active",
                    "fieldtype": "Check",
                    "label": "Active",
                    "default": "1",
                    "insert_after": "designation_name",
                    "in_list_view": 1,
                    "in_standard_filter": 1,
                }
            ]
        },
        ignore_validate=True,
        update=True,
    )

    # 2. Departments
    D = [
        "Executive Management",
        "Human Resources",
        "Information Technology",
        "Finance",
        "Operations",
        "Marketing & Business Development",
        "Merchant Management",
        "ERP Development Division",
    ]
    root = frappe.get_all("Department", filters={"is_group": 1, "company": C}, pluck="name")
    root_dept = root[0] if root else None
    qd_depts = {f"{d} - {A}" for d in D}

    print("Disabling default non-QD departments...")
    for d in frappe.get_all("Department", filters={"company": C, "is_group": 0}, pluck="name"):
        if d not in qd_depts:
            frappe.db.set_value("Department", d, "disabled", 1)

    print("Provisioning 8 QD Departments...")
    for d in D:
        n = f"{d} - {A}"
        if frappe.db.exists("Department", n):
            frappe.db.set_value("Department", n, "disabled", 0)
        else:
            doc = frappe.get_doc({
                "doctype": "Department",
                "department_name": d,
                "name": n,
                "company": C,
                "is_group": 0,
                "parent_department": root_dept,
            })
            doc.flags.ignore_links = True
            doc.insert(ignore_permissions=True)

    # 3. Employee Grades
    G = [
        ("Grade 1 - Entry", "QD-G1", 1, "Entry"),
        ("Grade 2 - Officer", "QD-G2", 2, "Operational"),
        ("Grade 3 - Intermediate", "QD-G3", 3, "Professional"),
        ("Grade 4 - Supervisor", "QD-G4", 4, "Supervisory"),
        ("Grade 5 - Manager", "QD-G5", 5, "Management"),
        ("Grade 6 - Executive", "QD-G6", 6, "Executive"),
    ]
    print("Provisioning 6 Employee Grades...")
    for n, c, l, cat in G:
        if frappe.db.exists("Employee Grade", n):
            doc = frappe.get_doc("Employee Grade", n)
            if doc.meta.has_field("custom_qd_grade_code"): doc.custom_qd_grade_code = c
            if doc.meta.has_field("custom_qd_grade_level"): doc.custom_qd_grade_level = l
            if doc.meta.has_field("custom_qd_grade_category"): doc.custom_qd_grade_category = cat
            if doc.meta.has_field("custom_qd_is_active"): doc.custom_qd_is_active = 1
            doc.flags.ignore_links = True
            doc.save(ignore_permissions=True)
        else:
            doc_dict = {"doctype": "Employee Grade", "name": n}
            meta = frappe.get_meta("Employee Grade")
            if meta.has_field("custom_qd_grade_code"): doc_dict["custom_qd_grade_code"] = c
            if meta.has_field("custom_qd_grade_level"): doc_dict["custom_qd_grade_level"] = l
            if meta.has_field("custom_qd_grade_category"): doc_dict["custom_qd_grade_category"] = cat
            if meta.has_field("custom_qd_is_active"): doc_dict["custom_qd_is_active"] = 1
            doc = frappe.get_doc(doc_dict)
            doc.flags.ignore_links = True
            doc.insert(ignore_permissions=True)

    # 4. Designations
    DES = [
        ("General Manager", "Grade 6 - Executive", 1),
        ("HR Manager", "Grade 5 - Manager", 1),
        ("HR Officer", "Grade 2 - Officer", 0),
        ("IT Manager", "Grade 5 - Manager", 1),
        ("System Administrator", "Grade 4 - Supervisor", 0),
        ("System Support Officer", "Grade 2 - Officer", 0),
        ("Finance Manager", "Grade 5 - Manager", 1),
        ("Senior Finance Officer", "Grade 3 - Intermediate", 0),
        ("Junior Finance Officer", "Grade 1 - Entry", 0),
        ("Operations Supervisor", "Grade 4 - Supervisor", 1),
        ("Operations Coordinator", "Grade 2 - Officer", 0),
        ("Fleet Coordinator", "Grade 2 - Officer", 0),
        ("Order Processor", "Grade 2 - Officer", 0),
        ("Business Development Officer", "Grade 2 - Officer", 0),
        ("Marketing Officer", "Grade 2 - Officer", 0),
        ("Merchant Officer", "Grade 2 - Officer", 0),
        ("Junior Merchant Officer", "Grade 1 - Entry", 0),
        ("Product Manager", "Grade 4 - Supervisor", 0),
        ("Senior Full Stack Developer", "Grade 3 - Intermediate", 0),
        ("Intermediate Full Stack Developer", "Grade 3 - Intermediate", 0),
        ("Junior Developer", "Grade 1 - Entry", 0),
        ("QA Engineer", "Grade 2 - Officer", 0),
        ("UI/UX Designer", "Grade 2 - Officer", 0),
        ("Business Analyst", "Grade 2 - Officer", 0),
    ]
    active_desigs = {d[0] for d in DES}
    print("Deactivating default designations...")
    for d in frappe.get_all("Designation", pluck="name"):
        if d not in active_desigs and frappe.get_meta("Designation").has_field("custom_qd_is_active"):
            frappe.db.set_value("Designation", d, "custom_qd_is_active", 0)

    print("Provisioning 24 QD Designations...")
    for n, g, a in DES:
        if frappe.db.exists("Designation", n):
            doc = frappe.get_doc("Designation", n)
            if doc.meta.has_field("custom_qd_default_employee_grade"): doc.custom_qd_default_employee_grade = g
            if doc.meta.has_field("custom_qd_is_active"): doc.custom_qd_is_active = 1
            if doc.meta.has_field("custom_qd_eligible_for_acting"): doc.custom_qd_eligible_for_acting = a
            doc.flags.ignore_links = True
            doc.save(ignore_permissions=True)
        else:
            doc_dict = {
                "doctype": "Designation",
                "designation_name": n,
                "name": n,
            }
            meta = frappe.get_meta("Designation")
            if meta.has_field("custom_qd_default_employee_grade"): doc_dict["custom_qd_default_employee_grade"] = g
            if meta.has_field("custom_qd_is_active"): doc_dict["custom_qd_is_active"] = 1
            if meta.has_field("custom_qd_eligible_for_acting"): doc_dict["custom_qd_eligible_for_acting"] = a
            doc = frappe.get_doc(doc_dict)
            doc.flags.ignore_links = True
            doc.insert(ignore_permissions=True)

    # 5. Positions
    POS = [
        ("General Manager", "QD-POS-001", "General Manager", "Executive Management", "Grade 6 - Executive", ""),
        ("HR Manager", "QD-POS-002", "HR Manager", "Human Resources", "Grade 5 - Manager", "General Manager"),
        ("HR Officer", "QD-POS-003", "HR Officer", "Human Resources", "Grade 2 - Officer", "HR Manager"),
        ("IT Manager", "QD-POS-004", "IT Manager", "Information Technology", "Grade 5 - Manager", "General Manager"),
        ("System Administrator", "QD-POS-005", "System Administrator", "Information Technology", "Grade 4 - Supervisor", "IT Manager"),
        ("System Support Officer", "QD-POS-006", "System Support Officer", "Information Technology", "Grade 2 - Officer", "IT Manager"),
        ("Finance Manager", "QD-POS-007", "Finance Manager", "Finance", "Grade 5 - Manager", "General Manager"),
        ("Senior Finance Officer", "QD-POS-008", "Senior Finance Officer", "Finance", "Grade 3 - Intermediate", "Finance Manager"),
        ("Junior Finance Officer", "QD-POS-009", "Junior Finance Officer", "Finance", "Grade 1 - Entry", "Finance Manager"),
        ("Operations Supervisor", "QD-POS-010", "Operations Supervisor", "Operations", "Grade 4 - Supervisor", "General Manager"),
        ("Operations Coordinator", "QD-POS-011", "Operations Coordinator", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
        ("Fleet Coordinator", "QD-POS-012", "Fleet Coordinator", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
        ("Order Processor", "QD-POS-013", "Order Processor", "Operations", "Grade 2 - Officer", "Operations Supervisor"),
        ("Business Development Officer", "QD-POS-014", "Business Development Officer", "Marketing & Business Development", "Grade 2 - Officer", "General Manager"),
        ("Marketing Officer", "QD-POS-015", "Marketing Officer", "Marketing & Business Development", "Grade 2 - Officer", "General Manager"),
        ("Merchant Officer", "QD-POS-016", "Merchant Officer", "Merchant Management", "Grade 2 - Officer", "General Manager"),
        ("Junior Merchant Officer", "QD-POS-017", "Junior Merchant Officer", "Merchant Management", "Grade 1 - Entry", "Merchant Officer"),
        ("Product Manager", "QD-POS-018", "Product Manager", "ERP Development Division", "Grade 4 - Supervisor", "General Manager"),
        ("Senior Full Stack Developer", "QD-POS-019", "Senior Full Stack Developer", "ERP Development Division", "Grade 3 - Intermediate", "Product Manager"),
        ("Intermediate Full Stack Developer", "QD-POS-020", "Intermediate Full Stack Developer", "ERP Development Division", "Grade 3 - Intermediate", "Product Manager"),
        ("Junior Developer", "QD-POS-021", "Junior Developer", "ERP Development Division", "Grade 1 - Entry", "Product Manager"),
        ("QA Engineer", "QD-POS-022", "QA Engineer", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
        ("UI/UX Designer", "QD-POS-023", "UI/UX Designer", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
        ("Business Analyst", "QD-POS-024", "Business Analyst", "ERP Development Division", "Grade 2 - Officer", "Product Manager"),
    ]
    print("Provisioning 24 Headcount Positions...")
    for n, c, des, dep, grd, rep in POS:
        if frappe.db.exists("QD Position", n):
            doc = frappe.get_doc("QD Position", n)
            doc.position_code = c
            doc.active = 1
            doc.company = C
            doc.designation = des
            doc.employee_grade = grd
            doc.department = f"{dep} - {A}"
            doc.reports_to_position = rep or ""
            doc.flags.ignore_links = True
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc({
                "doctype": "QD Position",
                "position_name": n,
                "name": n,
                "position_code": c,
                "active": 1,
                "company": C,
                "designation": des,
                "employee_grade": grd,
                "department": f"{dep} - {A}",
                "reports_to_position": rep or "",
            })
            doc.flags.ignore_links = True
            doc.insert(ignore_permissions=True)

    # 6. Leave Workflow
    print("Configuring Leave Workflow...")
    try:
        import qd_hrms.setup.leave
        qd_hrms.setup.leave.run()
    except Exception as e:
        print(f"Leave workflow note: {e}")

    frappe.db.commit()
    frappe.clear_cache()
    print("\n========================================================")
    print(f"  ORGANIZATION SETUP APPLIED FOR {C} ({A})!")
    print("========================================================\n")
