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
def AddNewPaymentEntry():
    frappe.clear_cache()
        