import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
import traceback
import sil.services.sales_invoice_api as sales_invoice_api
import sil.services.sales_order_api as sales_order_api

class PaymentEntryError(Exception):

    """Custom exception for Payment Entry errors."""

    pass


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

        # Filter out internal transfers
        payment_receipts = [receipt for receipt in payment_receipts if receipt.get('payment_type') != 'Internal Transfer']

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
        # Validate inputs
        if not all([customer, paid_amount > 0, payment_date, mode_of_payment, references]):
            raise ValueError("Invalid input parameters")

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
            # Validate reference details
            if not all([ref.get('reference_doctype'), ref.get('reference_name'), ref.get('total_amount'), ref.get('outstanding_amount'), ref.get('allocated_amount')]):
                raise ValueError("Invalid reference details")

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

    except ValueError as e:
        frappe.log_error(frappe.get_traceback(), f"Payment Entry Error for Customer: {customer}")
        return {'status': 'error', 'message': str(e)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Payment Entry Error for Customer: {customer}")
        return {'status': 'error', 'message': str(e)}



"""
for inserting the payment details from the 'Payment Receipt' doctype
"""
@frappe.whitelist(allow_guest=True)
def create_advance_payment(payment_type,customer, paid_amount, payment_date, mode_of_payment, reference_name=None):
    try:
        # Validate inputs
        if not all([customer, paid_amount > 0, payment_date, mode_of_payment]):
            raise ValueError("Invalid input parameters")

        # Create a new Payment Entry document
        payment_entry = frappe.get_doc({
            'doctype': 'Payment Entry',
            'payment_type': payment_type,  # Advance payment from customer
            'party_type': 'Customer',   # Payment is from a customer
            'party': customer,          # Customer name
            'paid_amount': paid_amount, # Amount paid in advance
            'payment_date': payment_date, # Date of payment
            'mode_of_payment': mode_of_payment,  # e.g., Cash, Bank Transfer, etc.
            'posting_date': payment_date  # Posting Date
        })

        # Add reference details if provided
        if reference_name:
            payment_entry.reference_no = reference_name
            payment_entry.reference_date = payment_date
            payment_entry.remarks = 'Advance payment for order'

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

    except ValueError as e:
        frappe.log_error(frappe.get_traceback(), f"Advance Payment Entry Error for Customer: {customer}")
        return {'status': 'error', 'message': str(e)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Advance Payment Entry Error for Customer: {customer}")
        return {'status': 'error', 'message': str(e)}      


@frappe.whitelist(allow_guest=True)
def updatePaymentReceiptDetailsToPaymentEntry():
    try:
        data = get_payment_details()
        if data:
            for payment in data:
                if payment.get("payment_type") != "Internal Transfer":
                    updateDetailsWithChildDetails(payment)
                else:
                    updateDetailsWithOutChildDetails(payment)
        else:
            frappe.log_error(message="No payment details found", title="Error in updatePaymentReceiptDetailsToPaymentEntry")
    except Exception as e:
        frappe.log_error(message=str(e), title="Error in updatePaymentReceiptDetailsToPaymentEntry")  
        


    # payment_entry = frappe.get_doc({
    #     'doctype': 'Payment Entry',
    #     'payment_type': 'Receipt',  # Advance payment from customer
    #     'party_type': 'Customer',   # Payment is from a customer
    #     'party': customer,          # Customer name
    #     'paid_amount': paid_amount, # Amount paid in advance
    #     'payment_date': payment_date, # Date of payment
    #     'mode_of_payment': mode_of_payment,  # e.g., Cash, Bank Transfer, etc.
    #     'reference_no': reference_name,  # Optional: Reference No
    #     'reference_date': payment_date, # Optional: Reference Date
    #     'remarks': 'Advance payment for order',  # Optional remarks
    #     'party_balance': paid_amount,  # Balance after the payment
    #     'posting_date': payment_date  # Posting Date
    # })

    # response = create_entries_payment(
    #     customer='Customer Name',  # The customer making the payment
    #     paid_amount=1000.00,        # Total amount paid
    #     payment_date='2024-12-11',  # Date of payment
    #     mode_of_payment='Bank Transfer',  # Mode of payment (e.g., Cash, Bank Transfer)
    #     references=[
    #         {'reference_doctype': 'Sales Invoice', 'reference_name': 'INV-001', 'total_amount': 500.00, 'outstanding_amount': 500.00, 'allocated_amount': 500.00},
    #         {'reference_doctype': 'Sales Order', 'reference_name': 'SO-001', 'total_amount': 500.00, 'outstanding_amount': 500.00, 'allocated_amount': 500.00}
    #             ]
    #         )
    # print(response)
        

def updateDetailsWithChildDetails(payment):     
    print(f"Payment Entry: {payment['name']}")
    print(f"Payment Type: {payment['payment_type']}")
    print(f"Date: {payment['date']}")
    print(f"Bank Account: {payment['bank_account']}")
    print(f"Mode of = "or" Payment: {payment['mode_of_payment']}")
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


def validate_inputs(payment_type, customer, invoice_name, payment_amount, payment_account):
    """Validate input parameters."""
    if not all([customer, invoice_name, payment_amount > 0, payment_account, payment_type]):
        raise PaymentEntryError("Invalid input parameters")


def get_exchange_rates(account_currency, company_currency):
    """Fetch exchange rates based on the currencies."""
    target_exchange_rate = 1.0
    source_exchange_rate = 1.0
    if account_currency and account_currency != company_currency:
        target_exchange_rate = frappe.db.get_value("Currency Exchange", 
                                                   {"from_currency": company_currency, "to_currency": account_currency}, 
                                                   "exchange_rate") or 1.0
        source_exchange_rate = frappe.db.get_value("Currency Exchange", 
                                                   {"from_currency": account_currency, "to_currency": company_currency}, 
                                                   "exchange_rate") or 1.0
    return target_exchange_rate, source_exchange_rate


def add_payment_references(payment_entry, invoice_name, payment_amount):
    """Add references to the payment entry."""
    payment_entry.append("references", {
        "reference_doctype": "Sales Invoice",
        "reference_name": invoice_name,
        "allocated_amount": payment_amount
    })


def create_payment_for_sales_invoice(payment_type, customer, invoice_name, payment_amount,
                                     payment_account, mode_of_payment, reference_number, 
                                     custom_deposited_by_customer, cheque_reference_date):
    try:
        # Validate inputs
        validate_inputs(payment_type, customer, invoice_name, payment_amount, payment_account)

        # Fetch the currency for the "Paid To" account
        account_currency = frappe.db.get_value("Account", payment_account, "account_currency")
        company_currency = frappe.get_cached_value("Company", frappe.defaults.get_global_default("company"), "default_currency")

        # Get exchange rates
        target_exchange_rate, source_exchange_rate = get_exchange_rates(account_currency, company_currency)

        # Prepare the payment entry data
        payment_entry_data = {
            "doctype": "Payment Entry",
            "payment_type": payment_type,
            "party_type": "Customer",
            "party": customer,
            "paid_amount": payment_amount,
            "received_amount": payment_amount,
            "paid_to": payment_account,
            "target_exchange_rate": target_exchange_rate,
            "source_exchange_rate": source_exchange_rate,
            "mode_of_payment": mode_of_payment,
            "reference_no": reference_number,
            "reference_date": cheque_reference_date,
            "references": [{
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice_name,
                "allocated_amount": payment_amount
            }]
        }

        # Insert the payment entry directly into the database
        payment_entry_name = frappe.db.insert(payment_entry_data)

        # Submit the Payment Entry
        frappe.get_doc("Payment Entry", payment_entry_name).submit()
        frappe.db.commit()  # Commit only after successful submission

        return {"status": "success", "message": f"Payment Entry created successfully: {payment_entry_name}"}

    except PaymentEntryError as e:
        # Log validation errors
        frappe.log_error(traceback.format_exc(), f"Validation Error: {str(e)}")
        return {"status": "error", "message": str(e)}

    except Exception as e:
        # Log other errors with detailed traceback
        error_message = f"Payment Entry Error for Customer: {customer}, Invoice: {invoice_name}, " \
                        f"Payment Type: {payment_type}, Amount: {payment_amount}, " \
                        f"Payment Account: {payment_account}, Mode of Payment: {mode_of_payment}, " \
                        f"Reference Number: {reference_number}, Deposited By: {custom_deposited_by_customer}, " \
                        f"Cheque Reference Date: {cheque_reference_date}. " \
                        f"Error: {str(e)}"

        frappe.log_error(traceback.format_exc(), error_message)
        return {"status": "error", "message": str(e)}



def create_payment_for_sales_order(payment_type, customer, invoice_name, payment_amount, payment_account,
    mode_of_payment, reference_number, custom_deposited_by_customer, cheque_reference_date):
    try:
        # Validate inputs
        # if not all([customer, invoice_name, payment_amount > 0, payment_account, payment_type]):
        #     raise ValueError("Invalid input parameters")

        # Fetch the currency for the "Paid To" account
        account_currency = frappe.db.get_value("Account", payment_account, "account_currency")
        company_currency = frappe.get_cached_value("Company", frappe.defaults.get_global_default("company"), "default_currency")

        # Determine if exchange rate is needed
        target_exchange_rate = 1.0
        if account_currency and account_currency != company_currency:
            # Fetch the exchange rate if currencies are different
            target_exchange_rate = frappe.db.get_value("Currency Exchange", 
                                                       {"from_currency": company_currency, "to_currency": account_currency}, 
                                                       "exchange_rate") or 1.0
        # Create a new Payment Entry
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": payment_type,
            "party_type": "Customer",
            "party": customer,
            "paid_amount": payment_amount,
            "received_amount": payment_amount,
            "paid_to": payment_account,
            "target_exchange_rate": target_exchange_rate, 
            "references": [
                {
                    "reference_doctype": "Sales Order",
                    "reference_name": invoice_name,
                    "allocated_amount": payment_amount
                }
            ],
            "mode_of_payment": mode_of_payment
            # ,
            # "reference_number": reference_number,
            # "cheque_reference_date": cheque_reference_date
        })

        # Insert and submit the Payment Entry
        payment_entry.insert(ignore_permissions=True)
        payment_entry.submit()

        return {"status": "success", "message": f"Payment Entry created successfully: {payment_entry.name}"}

    except ValueError as e:
        frappe.log_error(frappe.get_traceback(), f"Payment Entry Error for Customer: {customer}, Order: {invoice_name}")
        return {"status": "error", "message": str(e)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Payment Entry Error for Customer: {customer}, Order: {invoice_name}")
        return {"status": "error", "message": str(e)}     



def create_payment_for_InternalTransfer(payment_type, payment_amount, payment_account, mode_of_payment, customer=None, invoice_name=None):
    try:
        # Validate inputs
        if not all([payment_amount > 0, payment_account, payment_type]):
            raise ValueError("Invalid input parameters")

        # Create a new Payment Entry
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": payment_type,
            "party_type": "Customer" if customer else '',
            "party": customer if customer else '',
            "paid_amount": payment_amount,
            "received_amount": payment_amount,
            "paid_to": payment_account,
            "references": [
                {
                    "reference_doctype": "Sales Invoice" if invoice_name else '',
                    "reference_name": invoice_name if invoice_name else '',
                    "allocated_amount": payment_amount
                }
            ] if invoice_name else []
        })

        # Insert and submit the Payment Entry
        payment_entry.insert()
        payment_entry.submit()

        return {"status": "success", "message": f"Payment Entry created successfully: {payment_entry.name}"}

    except ValueError as e:
        frappe.log_error(frappe.get_traceback(), "Payment Entry Error for InternalTransfer")
        return {"status": "error", "message": str(e)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Entry Error for InternalTransfer")
        return {"status": "error", "message": str(e)}  


@frappe.whitelist()
def insertSalesInvoiceDetails(payment_entry_details, payment_entry):
    try:
        print("insertSalesInvoiceDetails")
        print("payment_entry_details:")
        print(payment_entry_details)
        print("payment_entry:")
        print(payment_entry)
        
        payment_details = payment_entry_details[0]

        return create_payment_for_sales_invoice(
                    payment_details.get('payment_type'),
                    payment_entry['customer'],
                    payment_entry['reference_name'],
                    payment_entry['allocated_amount'],
                    payment_details.get('account_paid_to'),
                    payment_details.get('mode_of_payment'),
                    payment_details.get('reference_number'),
                    payment_details.get('custom_deposited_by_customer'),
                    payment_details.get('chequereference_date')
                )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Entry Error for insertSalesInvoiceDetails")
        frappe.throw(_("An error occurred while processing Payment Entry: {0}").format(str(e)))

@frappe.whitelist()
def insertSalesOrderDetails(payment_entry_details, payment_entry):
    try:
        payment_details = payment_entry_details[0]

        create_payment_for_sales_order(
                    payment_entry_details['payment_type'],
                    payment_entry['customer'],
                    payment_entry['reference_name'],
                    payment_entry['allocated_amount'],
                    payment_entry_details['account_paid_to'],
                    payment_entry_details['mode_of_payment'],
                    payment_entry_details['reference_number'],
                    payment_entry_details['custom_deposited_by_customer'],
                    payment_entry_details['chequereference_date']
                )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Entry Error for insertSalesOrderDetails")
        frappe.throw(_("An error occurred while processing Payment Entry: {0}").format(str(e)))

@frappe.whitelist()
def insertInternalTransferDetails(payment_entry_details):
    try:
        payment_details = payment_entry_details[0]
        create_payment_for_InternalTransfer(
                    payment_entry_details['payment_type'],
                    payment_entry_details['amount_paid'],
                    payment_entry_details['account_paid_to'],
                    payment_entry_details['mode_of_payment']
                )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Entry Error for insertInternalTransferDetails")
        frappe.throw(_("An error occurred while processing Payment Entry: {0}").format(str(e)))

@frappe.whitelist()
def insertAdvanceDetails(payment_entry_details, payment_entry):
    try:
        payment_details = payment_entry_details[0]

        # Optionally, update the Customer balance to reflect the advance payment
        customer_doc = frappe.get_doc("Customer", payment_entry['customer'])
        customer_doc.outstanding_amount += payment_entry['allocated_amount']  # Increase the outstanding balance
        customer_doc.save()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Entry Error for insertAdvanceDetails")
        frappe.throw(_("An error occurred while processing Payment Entry: {0}").format(str(e)))


@frappe.whitelist(allow_guest=True)
def getAllReceiptDetailsFromDoc(payment_type=None, payment_entry_details=None, executive=None,
                                bank_account=None, account_paid_to=None, receipt_number=None,
                                custom_deposited_by_customer=None, amount_received=None, mode_of_payment=None,
                                amount_paid=None, reference_number=None, chequereference_date=None):
    """
    This method validates the passed details and processes the Payment Receipt.
    """

    # Check required fields
    required_fields = {
        "payment_type": payment_type,
        "mode_of_payment": mode_of_payment,
        "payment_entry_details": payment_entry_details,
        "executive": executive,
        "bank_account": bank_account,
        "receipt_number": receipt_number,
        "custom_deposited_by_customer": custom_deposited_by_customer,
        "amount_received": amount_received,
        "account_paid_to": account_paid_to,
        "amount_paid": amount_paid,
        "reference_number": reference_number,
        "chequereference_date": chequereference_date
    }

    print("getAllReceiptDetailsFromDoc required_fields:")
    print(required_fields)
    # Parse the payment_entry_details JSON string into a Python list
    # payment_entry_details = json.loads(data['payment_entry_details'])
    
    # Parse the payment_entry_details JSON string into a Python list if it's a string
    payment_entry_details = json.loads(required_fields) if isinstance(required_fields, str) else required_fields

    if payment_type in ["Receive", "Pay"]:
        if isinstance(payment_entry_details, list):
            for payment_entry in payment_entry_details:
                if payment_entry["reference_type"] == "Sales Invoice":
                    return insertSalesInvoiceDetails(payment_entry_details, payment_entry)
                elif payment_entry["reference_type"] == "Sales Order":
                    return insertSalesOrderDetails(payment_entry_details, payment_entry)
                elif payment_entry["reference_type"] == "Advance":
                    return insertAdvanceDetails(payment_entry_details, payment_entry)
                else:
                    print(f"Name: {payment_entry['name']}")
                    print(f"Customer: {payment_entry['customer']}")
                    print(f"Reference Type: {payment_entry['reference_type']}")
                    print(f"Reference Name: {payment_entry['reference_name']}")
                    print(f"Outstanding Amount: {payment_entry['outstanding_amount']}")
                    print(f"Allocated Amount: {payment_entry['allocated_amount']}")
                    print(f"Docstatus: {payment_entry['docstatus']}")
                    print(f"Parent: {payment_entry['parent']}")
                    print(f"Parent Type: {payment_entry['parenttype']}")
    else:
        return insertInternalTransferDetails(payment_entry_details)

    # Perform custom logic here
    try:
        # Process and return success message
        return {
            "status": "Success",
            "message": _("Payment Receipt details are validated and processed successfully."),
            "data": {
                "payment_type": payment_type,
                "executive": executive,
                "amount_received": amount_received
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Receipt Validation Error")
        frappe.throw(_("An error occurred while processing Payment Receipt: {0}").format(str(e)))