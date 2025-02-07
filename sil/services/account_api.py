import frappe
from frappe import _

@frappe.whitelist()
def getAccountName(account_name, company=None):
    if not account_name:
        frappe.throw("Account not found.")
    # Move the company check after SQL query definition
    if not company:
        frappe.throw("No company found.")
        
    suspense_account = frappe.db.sql(
        """
        SELECT name FROM `tabAccount`
        WHERE LOWER(account_name) LIKE LOWER(%s) AND company = %s
        LIMIT 1
        """, (f"%{account_name}%", company), as_dict=True)
        
    if not suspense_account:
        frappe.throw("No matching account found.")
    return suspense_account[0] # Return first matching account