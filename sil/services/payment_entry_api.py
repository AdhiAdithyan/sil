import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
import traceback


@frappe.whitelist(allow_guest=True)
def getAllPaymentEntryDetails():
    frappe.clear_cache()
    return frappe.get_all("Payment Entry",fields=["*"])


@frappe.whitelist(allow_guest=True)
def AddNewPaymentEntry(payment_entry_no):
    frappe.clear_cache()
    filters = {
                "parent": payment_entry_no
                }

    return frappe.get_all("Payment Entry",filters=filters , fields=["*"])





















