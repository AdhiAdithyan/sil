import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
import traceback


@frappe.whitelist(allow_guest=True)
def getAllPaymentEntryDetails():
    frappe.clear_cache()

    payment_details = frappe.get_all("Payment Entry",fields=["*"])

    for payment in payment_details:
        print(f"getAllPaymentEntryDetails payment:{payment}")
        payment["payment_referrence"] = GetAllPaymentRefferenceByPaymentNumber(payment['name'])
        for datails in payment:
            print(f"getAllPaymentEntryDetails datails:{datails}")
            print(f"getAllPaymentEntryDetails datails {datails}:{payment[datails]}")

    return payment_details if payment_details else []


@frappe.whitelist(allow_guest=True)
def AddNewPaymentEntry(payment_entry_no):
    frappe.clear_cache()
    filters = {
                "parent": payment_entry_no
                }

    return frappe.get_all("Payment Entry",filters=filters , fields=["*"])


@frappe.whitelist(allow_guest=True)
def GetAllPaymentRefferenceByPaymentNumber(payment_entry_no):
    frappe.clear_cache()
    filters = {
                "parent": payment_entry_no
                }

    return frappe.get_all("Payment Entry Reference",filters=filters , fields=["*"])
    # return frappe.get_all("Payment Entry Reference", fields=["*"])


def create_payment_entry(party_type, party, payment_type, paid_amount, received_amount, mode_of_payment, posting_date, reference_name=None):
    # Create a new Payment Entry document
    payment_entry = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": payment_type,  # "Receive" or "Pay"
        "party_type": party_type,  # "Customer" or "Supplier"
        "party": party,
        "paid_amount": paid_amount,
        "received_amount": received_amount,
        "mode_of_payment": mode_of_payment,
        "posting_date": posting_date,
    })
    
    # Optionally link to a specific Sales Invoice or Purchase Invoice
    if reference_name:
        payment_entry.append("references", {
            "reference_doctype": "Sales Invoice" if party_type == "Customer" else "Purchase Invoice",
            "reference_name": reference_name,
            "total_amount": paid_amount,
            "outstanding_amount": paid_amount,
            "allocated_amount": paid_amount,
        })

    # Insert and submit the Payment Entry
    payment_entry.insert()
    payment_entry.submit()

    # Return the name of the created Payment Entry
    return payment_entry.name


@frappe.whitelist(allow_guest=True)
def getAllPaidSlipDetails():
    try:
        query = """
                SELECT NAME, custom_slip_no, paid_amount 
                FROM `tabPayment Entry` 
                WHERE custom_slip_no !='' 
                AND docstatus=1 AND is_apportion_done=0
                ORDER BY modified DESC
                """
    
        return frappe.db.sql(query, as_dict=True)
    except Exception as e:
        frappe.log_error(f"Error in getAllPaidSlipDetails: {e}") 


@frappe.whitelist(allow_guest=True)
def IsSlipDetailsAvail(slip_no):
    try:
        query = """
                SELECT NAME, custom_slip_no, paid_amount 
                FROM `tabPayment Entry` 
                WHERE custom_slip_no !='' 
                AND docstatus=1 AND custom_is_apportion_done=0 AND custom_slip_no=%s
                ORDER BY modified DESC
                """
    
        result = frappe.db.sql(query,(slip_no,), as_dict=True)

        if result:
            return result
        else:
            return []
    except Exception as e:
        frappe.log_error(f"Error in IsSlipDetailsAvail: {e}")
        return []


@frappe.whitelist(allow_guest=True)
def updateSlipApportionStatus(doc, method):
    try:
        slip_no = doc.get('custom_slip_no')
        if slip_no:
            query = """
                UPDATE `tabPayment Entry` 
                SET custom_is_apportion_done = 1 
                WHERE custom_slip_no = %s
              """
            frappe.db.sql(query, (slip_no,))
            return {"message": "Slip apportionment status updated successfully", "status": "success"}
        # else:
        #     return {"message": "No slip details available", "status": "error"}
    except Exception as e:
        frappe.log_error(f"Error in updateSlipApportionStatus: {e}")
        return {"message": "Failed to update slip apportionment status", "status": "error"}


@frappe.whitelist(allow_guest=True)
def get_custom_slip_nos(filters=None):
    try:
        # Define base conditions: non-null custom_slip_no and custom_is_apportion_done=0
        conditions = {
            'custom_slip_no': ['is', 'set'],  # Only include non-null values
            'custom_is_apportion_done': 0   # Only include entries where apportioning is not done
        }
        
        # Parse filters if provided as a JSON string
        if filters and isinstance(filters, str):
            filters = json.loads(filters)
            
        # Add additional filter conditions based on input
        if filters:
            if filters.get('party'):
                conditions['party_name'] = filters.get('party')
            elif filters.get('slip_no'):
                # If querying for a specific slip number, return customer info
                payment_entry = frappe.get_all(
                    'Payment Entry',
                    filters={'custom_slip_no': filters.get('slip_no')},
                    fields=['party_name'],
                    order_by='creation DESC',
                    limit=1
                )
                if payment_entry:
                    return {'customer': payment_entry[0].party_name}
                return {}
        
        # Query "Payment Entry" for slip numbers matching the conditions
        slip_nos = frappe.get_all(
            'Payment Entry',
            filters=conditions,
            fields=['custom_slip_no'],
            order_by='custom_slip_no ASC'
        )
        
        # Filter out empty strings and convert to a unique, ordered list
        valid_slip_nos = [
            slip['custom_slip_no'] 
            for slip in slip_nos 
            if slip['custom_slip_no'] and slip['custom_slip_no'].strip()
        ]
        
        # Remove duplicates while maintaining order
        return list(dict.fromkeys(valid_slip_nos))
    except Exception as e:
        frappe.log_error(f"Error in get_custom_slip_nos: {e}")
        return []



@frappe.whitelist(allow_guest=True)
def get_payment_entry_by_slip(slip_no):
    if not slip_no:
        return []
        
    payment_entries = frappe.db.sql("""
        SELECT NAME, custom_slip_no, paid_amount, remarks 
        FROM `tabPayment Entry`
        WHERE custom_slip_no = %s 
        AND custom_is_apportion_done = 0
        AND docstatus = 1
        ORDER BY modified DESC
    """, (slip_no,), as_dict=1)
    
    return payment_entries        