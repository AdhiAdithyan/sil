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


@frappe.whitelist()
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


@frappe.whitelist()
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
        query1 = """
            SELECT
                name AS receipt_id_1,
                amount_received AS amount_1,
                executive,
                COALESCE(reference_number,'') as reference_number_1,
                COALESCE(chequereference_date,'') as reference_date_1
            FROM
                `tabPayment Receipt` 
            WHERE 
                payment_type='Internal Transfer' 
                AND custom_status='Pending' 
                AND custom_is_suspense_entry = 1 
                AND docstatus = 1
        """
        query2 = """
            SELECT
                name AS receipt_id_2,
                amount AS amount_2,
                executive,
                COALESCE(chequereference_number,'') as reference_number_2,
                COALESCE(reference_no,'') as reference_date_2
            FROM
                `tabPayment Intimation` 
            WHERE 
                custom_status='Pending' 
                AND custom_receipt_status='Journal'
        """
        table1_data = frappe.db.sql(query1, as_dict=True)
        table2_data = frappe.db.sql(query2, as_dict=True)

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


@frappe.whitelist(allow_guest=True)
def UpdatePaymentInfoForRejection(receipt_no, remark):
    try:
        # Validate input parameters
        if not receipt_no:
            frappe.throw(_("Receipt No is required."))
        if not remark:
            frappe.throw(_("Remark is required."))

        # Update the Payment Intimation table
        rows_affected = frappe.db.sql("""
            UPDATE `tabPayment Intimation` 
            SET custom_status='Rejected', custom_receipt_status='Rejected', custom_rejected_remark=%s 
            WHERE name = %s
        """, (remark, receipt_no,),as_dict=True)

        # Check if any rows were updated
        if not rows_affected:
            frappe.throw(_("No records found for the given receipt number."))

        # Commit the transaction to apply the changes
        frappe.db.commit()

        # Return a success response
        return {
            "status": "success",
            "message": f"Updated {len(rows_affected)} record(s) successfully.",
        }
    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in UpdatePaymentInfoForRejection')

        # Return an error response
        return {
            "status": "error",
            "message": "An error occurred while updating the record.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def MovePaymentInfoForJournalEntry(receipt_no):
    try:
        # Update the Payment Intimation table
        rows_affected = frappe.db.sql("""
            UPDATE `tabPayment Intimation` 
            SET custom_receipt_status = 'Journal' 
            WHERE name = %s
        """, (receipt_no,),as_dict=True)
        
        # Commit the transaction to apply the changes
        frappe.db.commit()
        
        # Return a success response
        return {
            "status": "success",
            "message": f"Updated {rows_affected} record(s) successfully.",
        }
    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in MovePaymentInfoForJournalEntry')
        
        # Return an error response
        return {
            "status": "error",
            "message": "An error occurred while updating the record.",
            "error": str(e)
        }



@frappe.whitelist(allow_guest=True)
def RemovePaymentInfoFromJournalEntry(receipt_no):
    try:
        rows_affected = frappe.db.sql("""
            UPDATE `tabPayment Intimation` 
            SET custom_receipt_status='Pending' 
            where name = %s and custom_receipt_status='Journal'
            """,(receipt_no,),as_dict=True)
        
        # Commit the transaction to apply the changes
        frappe.db.commit()
        
        # Return a success response
        return {
            "status": "success",
            "message": f"Updated {rows_affected} record(s) successfully.",
        }
    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in RemovePaymentInfoFromJournalEntry')
        
        # Return an error response
        return {
            "status": "error",
            "message": "An error occurred while updating the record.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def UpdateReceiptAfterJournalEntry(receipt_no):
    try:
        # Update the receipt status from 'Journal' to 'Paid'
        rows_affected = frappe.db.sql("""
        UPDATE `tabPayment Intimation`
        SET custom_receipt_status='Paid',custom_status
        WHERE name = %s AND custom_receipt_status='Journal'
        """,(receipt_no,),as_dict=True)

    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in UpdateReceiptAfterJournalEntry')


@frappe.whitelist(allow_guest=True)
def getSuspenseAndReceiptDetailsForJournalEntry(suspanse_id,receipt_id):
    try:
        # Get the suspense account details
        suspense_account_details = frappe.db.sql("""
        SELECT * FROM `tabPayment Receipt`
        WHERE name = %s and custom_status='Processing' and docstatus=1
        """,(suspanse_id,),as_dict=True)

        payment_receipt_details = frappe.db.sql("""
        SELECT * FROM `tabPayment Receipt`
        WHERE name = %s and custom_status='Processing' and docstatus=1
        """,(receipt_id,),as_dict=True)

        # Fetch all SIL payment details
        payment_details_query = """
            SELECT *
            FROM `tabSIL Payment Details`
        """
        payment_details = frappe.db.sql(payment_details_query, as_dict=True)

        # Group payment details by parent
        details_by_parent = {}
        for detail in payment_details:
            parent = detail.get('parent')
            if parent not in details_by_parent:
                details_by_parent[parent] = []
            details_by_parent[parent].append(detail)

        # Combine the data in a nested structure
        for receipt in payment_receipts:
            receipt['payment_details'] = details_by_parent.get(receipt['name'], [])

        # Filter out internal transfers
        payment_receipts = [receipt for receipt in payment_receipts if receipt.get('payment_type') != 'Internal Transfer']


    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in getSuspenseAndReceipt')
        return payment_receipts


