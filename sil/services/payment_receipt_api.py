import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
import traceback


def payment_info_before_save(doc, method):
    # Check and add child table entries programmatically
    if not doc.payment_entry_details:
        doc.append("payment_entry_details", {
            "fieldname1": "Value 1",
            "fieldname2": "Value 2"
        })

@frappe.whitelist(allow_guest=True)
def getAllPaymentReceiptDetails():
    try:
        query = """
                SELECT *
                FROM `tabPayment Receipt` 
            """               
        return frappe.db.sql(query, as_dict=True)  

    except Exception as e:
        frappe.log_error()
        return []


@frappe.whitelist(allow_guest=True)
def getAllPaymentEntryDetails():
    try:
        query = """
                SELECT *
                FROM `tabSIL Payment Details` 
            """               
        return frappe.db.sql(query, as_dict=True) 

    except Exception as e:
        frappe.log_error()
        return []


@frappe.whitelist(allow_guest=True)
def get_payment_details():
    try:
        # Fetch all payment receipts
        receipts_query = """
            SELECT *
            FROM `tabPayment Receipt`
        """
        payment_receipts = frappe.db.sql(receipts_query, as_dict=True)

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

        return payment_receipts

    except Exception as e:
        # Log the error with additional details
        frappe.log_error(message=str(e), title="Error in get_combined_payment_details_nested")
        return []


"""
for inserting the payment details from the 'Payment Receipt' doctype
"""
@frappe.whitelist(allow_guest=True)
def create_entries_payment(customer, paid_amount, payment_date, mode_of_payment, references):
    try:
        # Create a new Payment Entry document
        payment_entry = frappe.get_doc({
            'doctype': 'Payment Entry',
            'payment_type': 'Receipt',  # Receipt for Customer payments
            'party_type': 'Customer',   # Payment is from a customer
            'party': customer,          # Customer name
            'paid_amount': paid_amount, # Total paid amount
            'payment_date': payment_date, # Date of payment
            'mode_of_payment': mode_of_payment,  # Mode of payment
            'posting_date': payment_date,  # Posting Date
        })

        # Loop through the references to add multiple entries to the Payment Entry
        for ref in references:
            # Add Payment Entry References (e.g., linking to invoices or sales orders)
            payment_entry.append('references', {
                'reference_doctype': ref['reference_doctype'],  # Invoice or Sales Order
                'reference_name': ref['reference_name'],        # The name of the reference (e.g., SO-0001 or INV-0001)
                'total_amount': ref['total_amount'],             # The total amount for this reference
                'outstanding_amount': ref['outstanding_amount'], # The outstanding amount for this reference
                'allocated_amount': ref['allocated_amount'],     # The amount allocated from this payment
            })
        
        # Insert the document to save it to the database
        payment_entry.insert()

        # Optionally, submit the Payment Entry if required
        payment_entry.submit()

        # Return a success message with the Payment Entry name
        return {'status': 'success', 'message': 'Payment Entry created successfully with multiple references', 'payment_entry_name': payment_entry.name}

    except Exception as e:
        # Log any errors encountered
        frappe.log_error(message=str(e), title="Error in Creating Payment Entry with Multiple References")
        return {'status': 'error', 'message': f'Failed to create Payment Entry: {str(e)}'}


"""
for inserting the payment details from the 'Payment Receipt' doctype
"""
@frappe.whitelist(allow_guest=True)
def create_advance_payment(customer, paid_amount, payment_date, mode_of_payment, reference_name=None):
    try:
        # Create a new Payment Entry document
        payment_entry = frappe.get_doc({
            'doctype': 'Payment Entry',
            'payment_type': 'Receipt',  # Advance payment from customer
            'party_type': 'Customer',   # Payment is from a customer
            'party': customer,          # Customer name
            'paid_amount': paid_amount, # Amount paid in advance
            'payment_date': payment_date, # Date of payment
            'mode_of_payment': mode_of_payment,  # e.g., Cash, Bank Transfer, etc.
            'reference_no': reference_name,  # Optional: Reference No
            'reference_date': payment_date, # Optional: Reference Date
            'remarks': 'Advance payment for order',  # Optional remarks
            'party_balance': paid_amount,  # Balance after the payment
            'posting_date': payment_date  # Posting Date
        })

        # Insert the document to save it to the database
        payment_entry.insert()

        # Link to Sales Order as an advance (Optional)
        if reference_name:
            # Check if the Sales Order exists
            sales_order = frappe.get_doc("Sales Order", reference_name)
            if sales_order:
                # Add the advance payment to the Sales Order
                sales_order.advance_payment_amount = paid_amount
                sales_order.save()

        # Optionally, update the Customer balance to reflect the advance payment
        customer_doc = frappe.get_doc("Customer", customer)
        customer_doc.outstanding_amount += paid_amount  # Increase the outstanding balance
        customer_doc.save()

        # Optionally, submit the payment entry if required
        payment_entry.submit()

        # Return a success message with the Payment Entry name
        return {'status': 'success', 'message': 'Advance Payment Entry created successfully', 'payment_entry_name': payment_entry.name}

    except Exception as e:
        # Log any errors encountered
        frappe.log_error(message=str(e), title="Error in Creating Advance Payment Entry")
        return {'status': 'error', 'message': f'Failed to create Advance Payment Entry: {str(e)}'}        


@frappe.whitelist(allow_guest=True)
def updatePaymentReceiptDetailsToPaymentEntry():
    
    data = get_payment_details()
    # Iterate over the JSON data
    for payment in data["message"]:
        if payment["payment_type"] is not "Internal Transfer":
            updateDetailsWithChildDetails(payment)
        else:
            updateDetailsWithOutChildDetails(payment)    
        


    payment_entry = frappe.get_doc({
        'doctype': 'Payment Entry',
        'payment_type': 'Receipt',  # Advance payment from customer
        'party_type': 'Customer',   # Payment is from a customer
        'party': customer,          # Customer name
        'paid_amount': paid_amount, # Amount paid in advance
        'payment_date': payment_date, # Date of payment
        'mode_of_payment': mode_of_payment,  # e.g., Cash, Bank Transfer, etc.
        'reference_no': reference_name,  # Optional: Reference No
        'reference_date': payment_date, # Optional: Reference Date
        'remarks': 'Advance payment for order',  # Optional remarks
        'party_balance': paid_amount,  # Balance after the payment
        'posting_date': payment_date  # Posting Date
    })

    response = create_multiple_entries_payment(
        customer='Customer Name',  # The customer making the payment
        paid_amount=1000.00,        # Total amount paid
        payment_date='2024-12-11',  # Date of payment
        mode_of_payment='Bank Transfer',  # Mode of payment (e.g., Cash, Bank Transfer)
        references=[
            {'reference_doctype': 'Sales Invoice', 'reference_name': 'INV-001', 'total_amount': 500.00, 'outstanding_amount': 500.00, 'allocated_amount': 500.00},
            {'reference_doctype': 'Sales Order', 'reference_name': 'SO-001', 'total_amount': 500.00, 'outstanding_amount': 500.00, 'allocated_amount': 500.00}
                ]
            )
    print(response)
        

def updateDetailsWithChildDetails(payment):     
    print(f"Payment Entry: {payment['name']}")
    print(f"Payment Type: {payment['payment_type']}")
    print(f"Date: {payment['date']}")
    print(f"Bank Account: {payment['bank_account']}")
    print(f"Mode of Payment: {payment['mode_of_payment']}")
    print(f"Executive: {payment['executive']}")
    print(f"Amount Received: {payment['amount_received']}")
    print("Payment Details:")
    
    for detail in payment.get("payment_details", []):
        print(f"  - Customer: {detail['customer']}")
        print(f"    Reference Type: {detail['reference_type']}")
        print(f"    Reference Name: {detail['reference_name']}")
        print(f"    Outstanding Amount: {detail['outstanding_amount']}")
        print(f"    Allocated Amount: {detail['allocated_amount']}")
        print()


def updateDetailsWithOutChildDetails(payment):  
    print(f"Payment Entry: {payment['name']}")
    print(f"Payment Type: {payment['payment_type']}")
    print(f"Date: {payment['date']}")
    print(f"Bank Account: {payment['bank_account']}")
    print(f"Mode of Payment: {payment['mode_of_payment']}")
    print(f"Executive: {payment['executive']}")
    print(f"Amount Received: {payment['amount_received']}")       