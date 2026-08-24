import frappe

def apply_ui_fix():
    print("1. Granting Company Read permissions for Employee role...")
    for role in ("Employee", "Employee Self Service"):
        if not frappe.db.exists("Custom DocPerm", {"parent": "Company", "role": role, "permlevel": 0}):
            p = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": "Company",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "permlevel": 0,
                "read": 1,
                "select": 1,
            })
            p.flags.ignore_links = True
            p.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Custom DocPerm", {"parent": "Company", "role": role, "permlevel": 0}, "read", 1)
            frappe.db.set_value("Custom DocPerm", {"parent": "Company", "role": role, "permlevel": 0}, "select", 1)

    print("2. Restricting Desk Workspaces to appropriate roles...")
    WORKSPACE_ROLES = {
        "Accounting": ["Accounts User", "Accounts Manager", "Auditor", "System Manager"],
        "Stock": ["Stock User", "Stock Manager", "System Manager"],
        "Quality": ["Quality Manager", "Quality User", "System Manager"],
        "Support": ["Support Team", "Support Manager", "System Manager"],
        "Users": ["System Manager", "Administrator"],
        "ERPNext Settings": ["System Manager", "Administrator"],
        "Integrations": ["System Manager", "Administrator"],
        "Build": ["System Manager", "Administrator"],
        "Tools": ["System Manager", "Administrator"],
        "Website": ["Website Manager", "System Manager"],
        "Manufacturing": ["Manufacturing User", "Manufacturing Manager", "System Manager"],
        "Projects": ["Projects User", "Projects Manager", "System Manager"],
        "CRM": ["Sales User", "Sales Manager", "System Manager"],
        "Assets": ["Accounts User", "Accounts Manager", "System Manager"],
    }

    for ws_name, roles in WORKSPACE_ROLES.items():
        if frappe.db.exists("Workspace", ws_name):
            ws = frappe.get_doc("Workspace", ws_name)
            ws.set("roles", [])
            for r in roles:
                if frappe.db.exists("Role", r):
                    ws.append("roles", {"role": r})
            ws.public = 1
            ws.flags.ignore_links = True
            ws.save(ignore_permissions=True)

    print("3. Creating Module Profile 'QD - Employee Self Service'...")
    BLOCKED_MODULES = [
        "Accounts", "Stock", "Buying", "Selling", "Manufacturing",
        "Quality Management", "Support", "CRM", "Assets", "Projects",
        "Integrations", "ERPNext Settings", "Build", "Tools", "Website"
    ]
    valid_blocked = [m for m in BLOCKED_MODULES if frappe.db.exists("Module Def", m)]
    prof_name = "QD - Employee Self Service"
    
    if frappe.db.exists("Module Profile", prof_name):
        mp = frappe.get_doc("Module Profile", prof_name)
        mp.set("block_modules", [])
        for m in valid_blocked:
            mp.append("block_modules", {"module": m})
        mp.flags.ignore_links = True
        mp.save(ignore_permissions=True)
    else:
        mp = frappe.get_doc({
            "doctype": "Module Profile",
            "module_profile_name": prof_name,
            "name": prof_name,
            "block_modules": [{"module": m} for m in valid_blocked],
        })
        mp.flags.ignore_links = True
        mp.insert(ignore_permissions=True)

    print("4. Applying Module Profile to Self-Service users...")
    users = frappe.get_all("User", filters={"enabled": 1}, fields=["name"])
    for u in users:
        roles = frappe.get_roles(u.name)
        if "System Manager" not in roles and "Administrator" not in roles:
            frappe.db.set_value("User", u.name, "module_profile", prof_name)
