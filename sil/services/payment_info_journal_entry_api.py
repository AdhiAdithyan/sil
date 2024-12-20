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
def getSuspenseDetailsForApportion(receipt_1):
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
        frappe.log_error(frappe.get_traceback(), 'Error in getSuspenseDetailsForApportion') 


@frappe.whitelist(allow_guest=True)
def getPaymentInfoForApportion(receipt_2):
    try:
        table1_data = frappe.db.sql("""
            SELECT
                *
            FROM
                `tabPayment Intimation` 
            """, as_dict=True) 
        return {
            "table2_data": table1_data
        }     
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getPaymentInfoForApportion') 


@frappe.whitelist(allow_guest=True)
def getAllReceiptDetailsForJournalEntry():
    try:
        table1_data = frappe.db.sql("""
            SELECT
                name AS receipt_id_1,
                amount_received AS amount_1,
                COALESCE(reference_number,'') as reference_number_1,
                COALESCE(chequereference_date,'') as reference_date_1
            FROM
                `tabPayment Receipt` where payment_type='Internal Transfer' and custom_status='Pending' 
                and custom_is_suspense_entry = 1 and docstatus = 1
            """, as_dict=True)

        table2_data = frappe.db.sql("""
            SELECT
                name AS receipt_id_2,
                amount AS amount_2,
                COALESCE(chequereference_number,'') as reference_number_2,
                COALESCE(reference_no,'') as reference_date_2
            FROM
                `tabPayment Intimation` where custom_status='Pending' and custom_receipt_status='Pending' 
            """, as_dict=True)

        return {
            "table1_data": table1_data,
            "table2_data": table2_data
        } 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptDetailsForJournalEntry')
        frappe.throw(_('Loading Failed'))    


@frappe.whitelist(allow_guest=True)
def getDetailsForSelectedReceipts(receipt_1=None,receipt_2=None):
    try:
        import json
        receipt_1 = json.loads(receipt_1)
        receipt_2 = json.loads(receipt_2)

        # Perform any processing with the selected receipts here
        # Example: Validation or computation
        if float(receipt_1["amount"]) != float(receipt_2["amount"]):
            frappe.throw(_("Amounts of both selected receipts must be equal.")) 

        receipt_1 = getSuspenseDetailsForApportion(receipt_1)
        receipt_2 = getPaymentInfoForApportion(receipt_2)
        # Return the processed data 
        return {
            "receipt_1": receipt_1,
            "receipt_2": receipt_2
        }
    except Exception as e:   
        frappe.log_error(frappe.get_traceback(), 'Error in getDetailsForSelectedReceipts')         