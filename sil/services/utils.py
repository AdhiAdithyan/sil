import frappe
from frappe import _
import re


#add new field if not found.
def ensure_column_exists(doctype, column_name, column_type):
    try:
        if column_name not in frappe.db.get_table_columns(doctype):
            frappe.db.sql(f"ALTER TABLE `tab{doctype}` ADD COLUMN {column_name} {column_type} DEFAULT 0;")
            frappe.db.sql(f"ALTER TABLE `tab{doctype}` ADD CONSTRAINT unique_{doctype}_{column_name} UNIQUE ({column_name});")
    except Exception as e:
        frappe.log_error(f"Error in ensure_column_exists: {str(e)}")