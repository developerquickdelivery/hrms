import frappe

def apply_role_profiles():
    print("Connecting and creating Quick Delivery Role Profiles...")
    
    PROFILES = {
        "QD - General Manager": [
            "Employee",
            "Employee Self Service",
            "HR Manager",
            "Accounts Manager",
            "Leave Approver",
            "Expense Approver",
            "System Manager",
            "Workspace Manager",
        ],
        "QD - HR Manager": [
            "Employee",
            "Employee Self Service",
            "HR User",
            "HR Manager",
            "Leave Approver",
            "Expense Approver",
            "Workspace Manager",
        ],
        "QD - HR Officer": [
            "Employee",
            "Employee Self Service",
            "HR User",
            "Leave Approver",
            "Expense Approver",
        ],
        "QD - IT Manager": [
            "Employee",
            "Employee Self Service",
            "System Manager",
            "Workspace Manager",
            "Leave Approver",
            "Expense Approver",
        ],
        "QD - System Administrator": [
            "Employee",
            "Employee Self Service",
            "System Manager",
        ],
        "QD - Finance Manager": [
            "Employee",
            "Employee Self Service",
            "Accounts User",
            "Accounts Manager",
            "Expense Approver",
            "Leave Approver",
        ],
        "QD - Finance Officer": [
            "Employee",
            "Employee Self Service",
            "Accounts User",
            "Expense Approver",
        ],
        "QD - Operations Supervisor": [
            "Employee",
            "Employee Self Service",
            "Fleet Manager",
            "Leave Approver",
            "Expense Approver",
        ],
        "QD - Operations Coordinator": [
            "Employee",
            "Employee Self Service",
            "Fleet Manager",
        ],
        "QD - Product Manager": [
            "Employee",
            "Employee Self Service",
            "Leave Approver",
            "Expense Approver",
        ],
        "QD - Employee (Self Service)": [
            "Employee",
            "Employee Self Service",
        ],
    }

    for prof_name, roles_list in PROFILES.items():
        valid_roles = [r for r in roles_list if frappe.db.exists("Role", r)]
        
        if frappe.db.exists("Role Profile", prof_name):
            doc = frappe.get_doc("Role Profile", prof_name)
            doc.set("roles", [])
        else:
            doc = frappe.get_doc({
                "doctype": "Role Profile",
                "role_profile": prof_name,
                "roles": [],
            })
        
        for r in valid_roles:
            doc.append("roles", {"role": r})
        
        doc.flags.ignore_links = True
        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)
