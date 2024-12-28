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
                `tabPayment Receipt` where name=%s 

            """, (receipt_1,),as_dict=True) 
        return {
            "table1_data": table1_data
        }     
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getSuspenseDetailsForApportion') 


@frappe.whitelist()
def getPaymentInfoForApportion(receipt_2):
    try:

        query = """
            SELECT
                *
            FROM
                `tabReceipt` 
            WHERE 
                parent = %s
        """
        table2_data = frappe.db.sql(query,(receipt_2,), as_dict=True) 

        return {
            "table2_data": table2_data
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

        # Validate query results
        if not table1_data or not table2_data:
            frappe.throw(_("No records found for the given queries."))

        return {
            "table1_data": table1_data,
            "table2_data": table2_data
        } 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptDetailsForJournalEntry')
        frappe.throw(_('Loading Failed'))


@frappe.whitelist(allow_guest=True)
def getDetailsForSelectedReceipts(receipt_1=None, receipt_2=None):
    try:
        import json
        receipt_1 = json.loads(receipt_1)
        receipt_2 = json.loads(receipt_2)


        print(receipt_1)
        print(receipt_2)

        # Validate input parameters
        if not receipt_1 or not receipt_2:
            frappe.throw(_("Both receipts are required."))

        # Perform any processing with the selected receipts here
        # Example: Validation or computation
        if float(receipt_1["amount"]) != float(receipt_2["amount"]):
            frappe.throw(_("Amounts of both selected receipts must be equal."))

        # Fetch additional details for the receipts
        receipt_1_details = getSuspenseDetailsForApportion(receipt_1["receipt_id"])
        receipt_2_details = getPaymentInfoForApportion(receipt_2["receipt_id"])

        # Combine the data in a nested structure
        receipt_1 = {**receipt_1, **receipt_1_details}
        receipt_2 = {**receipt_2, **receipt_2_details}

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
            "message": _("Updated {} record(s) successfully.").format(len(rows_affected)),
            "data": rows_affected
        }
    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in UpdatePaymentInfoForRejection')

        # Return an error response
        return {
            "status": "error",
            "message": _("An error occurred while updating the record."),
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def MovePaymentInfoForJournalEntry(receipt_no):
    try:
        # Validate input parameters
        if not receipt_no:
            frappe.throw(_("Receipt No is required."))

        # Update the Payment Intimation table
        rows_affected = frappe.db.sql("""
            UPDATE `tabPayment Intimation` 
            SET custom_receipt_status = 'Journal' 
            WHERE name = %s
        """, (receipt_no,), as_dict=True)

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
            WHERE name = %s AND custom_receipt_status='Journal'
        """, (receipt_no,), as_dict=True)
        
        if rows_affected:
            frappe.db.commit()
            return {
                "status": "success",
                "message": f"Updated {len(rows_affected)} record(s) successfully.",
            }
        else:
            return {
                "status": "error",
                "message": "No records found for the given receipt number.",
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in RemovePaymentInfoFromJournalEntry')
        return {
            "status": "error",
            "message": "An error occurred while updating the record.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def UpdateReceiptAfterJournalEntry(receipt_no):
    try:
        # Validate input parameters
        if not receipt_no:
            frappe.throw(_("Receipt No is required."))

        # Update the receipt status from 'Journal' to 'Paid'
        rows_affected = frappe.db.sql("""
        UPDATE `tabPayment Intimation`
        SET custom_receipt_status='Paid', custom_status='Paid'
        WHERE name = %s AND custom_receipt_status='Journal'
        """,(receipt_no,),as_dict=True)

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
        frappe.log_error(frappe.get_traceback(), 'Error in UpdateReceiptAfterJournalEntry')

        # Return an error response
        return {
            "status": "error",
            "message": "An error occurred while updating the record.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def getSuspenseAndReceiptDetailsForJournalEntry(suspanse_id, receipt_id):
    try:
        # Get the suspense account details
        suspense_account_details = frappe.db.get_value('Payment Receipt', suspanse_id, '*', as_dict=True)

        # Get the payment receipt details
        payment_receipt_details = frappe.db.get_value('Payment Receipt', receipt_id, '*', as_dict=True)

        # Fetch all SIL payment details
        payment_details = frappe.db.get_all('SIL Payment Details', fields='*', as_dict=True)

        # Group payment details by parent
        details_by_parent = {}
        for detail in payment_details:
            parent = detail.get('parent')
            if parent not in details_by_parent:
                details_by_parent[parent] = []
            details_by_parent[parent].append(detail)

        # Combine the data in a nested structure
        if payment_receipt_details:
            payment_receipt_details['payment_details'] = details_by_parent.get(payment_receipt_details['name'], [])

        # Filter out internal transfers
        if payment_receipt_details and payment_receipt_details.get('payment_type') != 'Internal Transfer':
            return {
                'suspense_account_details': suspense_account_details,
                'payment_receipt_details': payment_receipt_details
            }
        else:
            return {
                'suspense_account_details': suspense_account_details,
                'payment_receipt_details': None
            }

    except Exception as e:
        # Log the error in the system
        frappe.log_error(frappe.get_traceback(), 'Error in getSuspenseAndReceipt')
        return {
            'suspense_account_details': None,
            'payment_receipt_details': None,
            'error': str(e)
        }



#call when submit button is pressed in journal entry
@frappe.whitelist(allow_guest=True)
def getDetailsFromJournalEntry():
    try:
        pass 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getDetailsFromJournalEntry')    