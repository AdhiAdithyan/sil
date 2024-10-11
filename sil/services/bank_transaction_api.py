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
    return frappe.db.sql("""Select * from `tabPayment Entry`;""",as_dict=True)        


@frappe.whitelist(allow_guest=True)
def getBankTransactionPaymentsDetails():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the e-invoice details which are not updated in the tally application.
    return frappe.db.sql("""Select * from `tabBank Transaction Payments`;""",as_dict=True)        


# @frappe.whitelist(allow_guest=False)
# def getAllBankTransactionDetails():
#     # Clear the cache
#     frappe.clear_cache()

#     # Return all the payment details with JSON aggregation of payment entries
#     bank_transactions =  frappe.db.sql("""
#         SELECT 
#             bt.name,
#             bt.date,
#             bt.status,
#             bt.currency,
#             bt.deposit,
#             bt.allocated_amount,
#             bt.unallocated_amount,
#             bt.bank_account,
#             bt.reference_number,
#             bt.transaction_id,
#             bt.transaction_type,
#             bt.company,
#             JSON_ARRAYAGG(JSON_OBJECT(
#                 'payment_entry_name', pe.name,
#                 'posting_date', pe.posting_date,
#                 'party_type', pe.party_type,
#                 'party', pe.party,
#                 'paid_amount', pe.paid_amount,
#                 'received_amount', pe.received_amount,
#                 'payment_type', pe.payment_type,
#                 'company', pe.company,
#                 'party_balance', pe.party_balance
#             )) AS payment_entries
#         FROM 
#             `tabBank Transaction` bt
#         LEFT JOIN `tabBank Transaction Payments` btp ON btp.parent = bt.name
#         LEFT JOIN `tabPayment Entry` pe ON pe.name = btp.payment_entry
#         GROUP BY bt.name
#     ;""", as_dict=True)

#     # Parse payment_entries field from string to JSON object
#     for transaction in bank_transactions:
#         if transaction['payment_entries']:
#             transaction['payment_entries'] = json.loads(transaction['payment_entries'])

#     return bank_transactions


@frappe.whitelist(allow_guest=False)
def getAllBankTransactionDetails():
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

    # For each bank transaction, get related Payment Entries
    for transaction in bank_transactions:
        # Get all Bank Transaction Payments associated with this Bank Transaction
        payments = frappe.get_all(
            'Bank Transaction Payments',
            filters={'parent': transaction['name']},
            fields=['payment_entry']
        )

        payment_entries = []

        # Loop through each payment entry and fetch the related Payment Entry details
        for payment in payments:
            payment_entry = frappe.get_doc('Payment Entry', payment['payment_entry'])
            
            print(f"payment_entry :{payment_entry}")

            # Get all fields from the document
            all_fields = payment_entry.as_dict()

            # Get meta information of Payment Entry (for field details)
            payment_entry_meta = frappe.get_meta('Payment Entry')

            # Get detailed information of all fields
            field_details = []
            for df in payment_entry_meta.fields:
                field_info = {
                    'fieldname': df.fieldname,
                    'label': df.label,
                    'fieldtype': df.fieldtype,
                    'options': df.options if df.fieldtype == 'Link' else None,
                    'value': all_fields.get(df.fieldname)
                }
                field_details.append(field_info)

            # Separate link fields from the rest for convenience
            link_fields = [field for field in field_details if field['fieldtype'] == 'Link']
            
            payment_entries.append({
                'payment_entry_name': payment_entry.name,
                'posting_date': payment_entry.posting_date,
                'party_type': payment_entry.party_type,
                'party': payment_entry.party,
                'paid_amount': payment_entry.paid_amount,
                'received_amount': payment_entry.received_amount,
                'payment_type': payment_entry.payment_type,
                'company': payment_entry.company,
                'party_balance': payment_entry.party_balance,
                'linked_fields' :link_fields
            })

        # Attach the payment entries as a list in the transaction
        transaction['payment_entries'] = payment_entries

    return bank_transactions