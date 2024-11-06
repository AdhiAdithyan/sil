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


















