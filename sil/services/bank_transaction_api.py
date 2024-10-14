import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
import traceback



@frappe.whitelist(allow_guest=True)
def getBankTransactionDetails():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the e-invoice details which are not updated in the tally application.
    return frappe.db.sql("""Select * from `tabBank Transaction`;""",as_dict=True) 


@frappe.whitelist(allow_guest=True)
def getPaymentEntryDetails():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the e-invoice details which are not updated in the tally application.
    # return frappe.db.sql("""Select * from `tabPayment Entry`;""",as_dict=True)        
    # Fetch the payment entry details
    return frappe.get_all('Payment Entry',  fields=["*"])


@frappe.whitelist(allow_guest=True)
def getAllPaymentreference():
    frappe.clear_cache()    
    return frappe.get_all('Payment Entry Reference',  fields=["*"])


@frappe.whitelist(allow_guest=True)
def getBankTransactionPaymentsDetails():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the e-invoice details which are not updated in the tally application.
    return frappe.db.sql("""Select * from `tabBank Transaction Payments`;""",as_dict=True)        


@frappe.whitelist(allow_guest=False)
def getAllBankTransactionDetails():
    try:
        # Clear the cache
        frappe.clear_cache()

        # Get all Bank Transactions
        bank_transactions = frappe.get_all(
            'Bank Transaction',
            fields=[
                'name', 'date', 'status', 'currency', 'deposit', 
                'allocated_amount', 'unallocated_amount', 'bank_account',
                'reference_number', 'transaction_id', 'transaction_type',
                'company'
            ]
        )

        if not bank_transactions:
            frappe.log_error('No bank transactions found.', 'Bank Transaction Error')
            return {'status': 'error', 'message': 'No bank transactions found.'}

        # For each bank transaction, get related Payment Entries
        for transaction in bank_transactions:
            # Check for missing or incomplete transaction details
            if not transaction.get('name'):
                frappe.log_error(f'Missing transaction name: {transaction}', 'Bank Transaction Error')
                continue

            # Get all Bank Transaction Payments associated with this Bank Transaction
            payments = frappe.get_all(
                'Bank Transaction Payments',
                filters={'parent': transaction['name']},
                fields=['payment_entry']
            )

            payment_entries = []

            if not payments:
                frappe.log_error(f'No payments found for transaction {transaction["name"]}', 'Bank Transaction Error')
                continue

            # Loop through each payment entry and fetch the related Payment Entry details
            for payment in payments:
                if not payment.get('payment_entry'):
                    frappe.log_error(f'Missing payment entry in {payment}', 'Payment Entry Error')
                    continue

                filters = {
                    "name": payment['payment_entry']
                }

                # Fetch the payment entry details
                payment_entry = frappe.get_all('Payment Entry', filters=filters, fields=["*"])

                if not payment_entry:
                    frappe.log_error(f'No Payment Entry found for payment {payment["payment_entry"]}', 'Payment Entry Error')
                    continue

                payment_entry = payment_entry[0]  # Assuming a single result is returned

                if not payment_entry.get('name'):
                    frappe.log_error(f'Missing Payment Entry name: {payment_entry}', 'Payment Entry Error')
                    continue

                filters = {
                    "parent": payment_entry.get('name')
                }

                # Fetch the payment entry reference details
                payment_entry_reference = frappe.get_all(
                    'Payment Entry Reference',
                    filters=filters,
                    fields=['reference_name', 'total_amount', 'allocated_amount', 'outstanding_amount', 'due_date']
                )

                if not payment_entry_reference:
                    frappe.log_error(f'No Payment Entry Reference found for Payment Entry {payment_entry["name"]}', 'Payment Entry Reference Error')
                    continue

                # Loop through each payment entry reference and append details
                for reference in payment_entry_reference:
                    payment_entries.append({
                        'payment_entry_name': payment_entry.get('name'),
                        'posting_date': payment_entry.get('posting_date'),
                        'party_type': payment_entry.get('party_type'),
                        'party': payment_entry.get('party'),
                        'paid_amount': payment_entry.get('paid_amount'),
                        'received_amount': payment_entry.get('received_amount'),
                        'payment_type': payment_entry.get('payment_type'),
                        'company': payment_entry.get('company'),
                        'party_balance': payment_entry.get('party_balance'),
                        'reference_name': reference.get('reference_name'),
                        'total_amount': reference.get('total_amount'),
                        'allocated_amount': reference.get('allocated_amount'),
                        'outstanding_amount': reference.get('outstanding_amount'),
                        'due_date': reference.get('due_date')
                    })

            # Attach the payment entries as a list in the transaction
            transaction['payment_entries'] = payment_entries

        return bank_transactions

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllBankTransactionDetails')
        return {'status': 'error', 'message': str(e)}

