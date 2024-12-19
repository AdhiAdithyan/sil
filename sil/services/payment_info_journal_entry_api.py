import frappe 
from frappe import _
import json 


@frappe.whitelist(allow_guest=True)
def get_data():
    try:
        table1_data = frappe.db.sql("""
            SELECT
                *
            FROM
                `tabPayment Receipt` 
            """, as_dict=True) 
        return {
            "table1_data": table1_data
        }     
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptDetailsForJournalEntry')    


@frappe.whitelist(allow_guest=True)
def getAllReceiptDetailsForJournalEntry():
    try:
        table1_data = frappe.db.sql("""
            SELECT
                name AS receipt_id_1,
                amount_received AS amount_1
            FROM
                `tabPayment Receipt` where payment_type='Internal Transfer' and custom_status='Pending' 
                and custom_is_suspense_entry = 1
            """, as_dict=True)

        table2_data = frappe.db.sql("""
            SELECT
                name AS receipt_id_2,
                amount AS amount_2
            FROM
                `tabPayment Info` where custom_status='Pending' and custom_receipt_status='Pending'
            """, as_dict=True)

        return {
            "table1_data": table1_data,
            "table2_data": table2_data
        } 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptDetailsForJournalEntry')
        frappe.throw(_('Loading Failed'))    