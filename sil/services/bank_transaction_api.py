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


@frappe.whitelist(allow_guest=False)
def getAllBankTransactionDetails():
    # Clear the cache
    frappe.clear_cache()

    # Return all the payment details with JSON aggregation of payment entries
    bank_transactions =  frappe.db.sql("""
        SELECT 
            bt.name,
            bt.date,
            bt.status,
            bt.currency,
            bt.deposit,
            bt.allocated_amount,
            bt.unallocated_amount,
            bt.bank_account,
            bt.reference_number,
            bt.transaction_id,
            bt.transaction_type,
            bt.company,
            JSON_ARRAYAGG(JSON_OBJECT(
                'payment_entry_name', pe.name,
                'posting_date', pe.posting_date,
                'party_type', pe.party_type,
                'party', pe.party,
                'paid_amount', pe.paid_amount,
                'received_amount', pe.received_amount,
                'payment_type', pe.payment_type,
                'company', pe.company,
                'party_balance', pe.party_balance
            )) AS payment_entries
        FROM 
            `tabBank Transaction` bt
        LEFT JOIN `tabBank Transaction Payments` btp ON btp.parent = bt.name
        LEFT JOIN `tabPayment Entry` pe ON pe.name = btp.payment_entry
        GROUP BY bt.name
    ;""", as_dict=True)

    # Parse payment_entries field from string to JSON object
    for transaction in bank_transactions:
        if transaction['payment_entries']:
            transaction['payment_entries'] = json.loads(transaction['payment_entries'])

    return bank_transactions