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
        # First check in Payment Receipt table
        payment_receipt_exists = frappe.db.exists("Payment Receipt", receipt_1)
        
        if payment_receipt_exists:
            # If found in Payment Receipt, get those details
            table1_data = frappe.db.sql("""
                SELECT *
                FROM `tabPayment Receipt` 
                WHERE name = %s
            """, (receipt_1,), as_dict=True)
            
            return {
                "table1_data": table1_data
            }
        else:
            # If not found in Payment Receipt, check Journal Entry Account
            journal_entries = frappe.db.sql("""
                SELECT 
                    *,
                    credit as amount_paid,
                    account as account_paid_to

                FROM `tabJournal Entry Account`
                WHERE 
                    parent = %s 
                    AND account = 'Suspense - SIL'
            """, (receipt_1,), as_dict=True)
            
            return {
                "table1_data": journal_entries
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
        # Fetch results for Query 1 using getSuspenseEntries function
        table1_data = getSuspenseEntries()
        
        # Query 2 remains unchanged
        query2 = """
            SELECT
                name AS receipt_id_2,
                amount AS amount_2,
                executive,
                COALESCE(chequereference_number, '') AS reference_number_2,
                COALESCE(DATE_FORMAT(reference_no, '%d-%m-%Y'), '') AS reference_date_2
            FROM
                `tabPayment Intimation` 
            WHERE 
                custom_status = 'In Progress'
                AND custom_receipt_status = 'Journal'
        """
        
        # Execute Query 2
        table2_data = frappe.db.sql(query2, as_dict=True)

        # Validate results
        if not table1_data and not table2_data:
            frappe.throw(_("No records found for the given queries."))
        
        # Return combined data
        return {
            "table1_data": table1_data,  # Data from getSuspenseEntries
            "table2_data": table2_data  # Data from query 2
        }
    
    except Exception as e:
        # Log and throw error
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptDetailsForJournalEntry')
        frappe.throw(_('Loading Failed'))


@frappe.whitelist(allow_guest=True)
def getDetailsForSelectedReceipts(receipt_1=None, receipt_2=None):
    try:
        import json
        receipt_1 = json.loads(receipt_1)
        receipt_2 = json.loads(receipt_2)


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
        frappe.db.sql("""
            UPDATE `tabPayment Intimation` 
            SET custom_status = %s, custom_rejected_remarks = %s 
            WHERE name = %s
        """, ('Rejected', remark, receipt_no))

        # Commit the transaction to apply the changes
        frappe.db.commit()

        # Return a success response
        return {
            "status": "success",
            "message": _("Payment Intimation record updated successfully."),
            "data": {"receipt_no": receipt_no, "status": "Rejected"}
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
            SET custom_receipt_status = 'Journal',
                custom_status ="In Progress" 
            WHERE name = %s
        """, (receipt_no,), as_dict=True)

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
        # Execute the update query (no need for as_dict or additional parameters)
        rows_affected = frappe.db.sql("""
            UPDATE `tabPayment Intimation` 
            SET custom_receipt_status='Pending',
                custom_status = 'Pending'

            WHERE name = %s AND custom_receipt_status='Journal'
        """, (receipt_no,))

        # The rows_affected is now an integer, not a list
        frappe.log_error(f"Rows affected: {rows_affected}", "Debug - RemovePaymentInfoFromJournalEntry")

        # Check if rows were affected
        
        frappe.db.commit()
        return {
            "status": "success",
            "message": f"Updated {rows_affected} record(s) successfully.",
        }
   

    except Exception as e:
        # Log the error traceback
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


@frappe.whitelist(allow_guest=True)
def update_payment_and_receipt_on_submit(doc, method):
    try:
        # Fetch the required field values from the submitted document
        custom_payment_info_id = doc.get('custom_payment_info_id')
        custom_suspense_id = doc.get('custom_suspense_id')
        
        # Validate that required fields are present
        if custom_payment_info_id and custom_suspense_id:
            # Update the Payment Intimation table
            frappe.db.sql(
                """
                UPDATE `tabPayment Intimation`
                SET
                    custom_status = 'Paid',
                    custom_receipt_status = 'Paid'
                WHERE name = %s
                """,
                (custom_payment_info_id,)
            )
            
            # Check if custom_suspense_id exists as name in tabPayment Receipt
            payment_receipt_exists = frappe.db.sql(
                """
                SELECT name 
                FROM `tabPayment Receipt`
                WHERE name = %s
                """,
                (custom_suspense_id,),
                as_dict=1
            )
            
            if payment_receipt_exists:
                # Update the Payment Receipt table if record exists
                frappe.db.sql(
                    """
                    UPDATE `tabPayment Receipt`
                    SET
                        custom_status = 'Paid'
                    WHERE name = %s
                    """,
                    (custom_suspense_id,)
                )
            else:
                # If not in Payment Receipt, update Journal Entry Account
                frappe.db.sql(
                    """
                    UPDATE `tabJournal Entry Account`
                    SET
                        is_apportion_done = 1
                    WHERE parent = %s
                    """,
                    (custom_suspense_id,)
                )
            
            # Commit the changes to the database
            frappe.db.commit()
            
    except frappe.exceptions.ValidationError as e:
        # Handle known validation errors
        frappe.log_error(message=str(e), title="Validation Error in update_payment_and_receipt_on_submit")
        frappe.throw(f"Validation Error: {str(e)}")
    except Exception as e:
        # Handle any unexpected errors
        frappe.log_error(message=str(e), title="Error in update_payment_and_receipt_on_submit")
        frappe.throw(f"An unexpected error occurred: {str(e)}")

@frappe.whitelist(allow_guest=True)
def getSuspenseEntries():
    try:
        # First query for Payment Receipt entries
        payment_receipt_query = """
            SELECT
                name as receipt_id_1,
                amount_received as amount_1,
                executive,
                date,
                mode_of_payment,
                COALESCE(reference_number, '') AS reference_number_1,
                COALESCE(chequereference_date, '') AS reference_date_1
            FROM
                `tabPayment Receipt`
            WHERE
                payment_type = 'Internal Transfer'
                AND custom_status = 'Processing'
                AND custom_is_suspense_entry = 1
                AND docstatus = 1
            ORDER BY
                modified DESC;
        """
        
        # Second query for Journal Entry Account entries
        journal_entry_query = """
            SELECT 
                jo.parent as receipt_id_1,
                jo.credit as amount_1,
                '' as executive,
                jo.creation as date,
                '' as mode_of_payment,
                '' as reference_number_1,
                '' as reference_date_1
            FROM 
                `tabJournal Entry Account` jo
            INNER JOIN 
                `tabAccount` ta ON jo.account = ta.name
            WHERE  
                jo.docstatus = 1
                AND ta.custom_is_suspense = 1
                AND jo.is_apportion_done != 1
                AND jo.debit = 0
                AND jo.credit != 0
            ORDER BY
                jo.modified DESC;


        """
        
        # Execute both queries
        payment_receipt_results = frappe.db.sql(payment_receipt_query, as_dict=True)
        journal_entry_results = frappe.db.sql(journal_entry_query, as_dict=True)
        
        # Combine the results
        combined_results = payment_receipt_results + journal_entry_results
        
        # Format dates if needed
        for result in combined_results:
            if result.get('date'):
                result['date'] = frappe.utils.formatdate(result['date'])
            if result.get('reference_date_1'):
                result['reference_date_1'] = frappe.utils.formatdate(result['reference_date_1'])
                
            # Ensure amount is formatted as float
            if result.get('amount_1'):
                result['amount_1'] = float(result['amount_1'])
                
            # Ensure executive has a value
            if not result.get('executive'):
                result['executive'] = 'N/A'
        
        return combined_results
        
    except Exception as e:
        frappe.log_error(
            message=f"Error Fetching Suspense Entries: {str(e)}\n{frappe.get_traceback()}", 
            title="Error Fetching Suspense Entries"
        )
        return []

@frappe.whitelist(allow_guest=True)
def get_test():
    try:
        # You can use the `receipt_2` parameter in your query if needed for filtering.
        # For example, if you want to filter based on a receipt:
        query = """
            SELECT
                *
            FROM
                `tabJournal Entry Account`

        """
        
        # Execute the query
        result = frappe.db.sql(query, as_dict=True)
        
        # Return the result
        return result
    
    except Exception as e:
        # If there's an error, log it and return a message
        frappe.log_error(f"Error in get_test function: {str(e)}", title="get_test Error")
        return {"error": str(e)}
