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





















