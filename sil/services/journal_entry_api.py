import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
import traceback


@frappe.whitelist(allow_guest=True)
def getAllJournalEntryDetails():
    frappe.clear_cache()
    return frappe.get_all("Journal Entry",fields=["*"])


@frappe.whitelist(allow_guest=True)
def getAllJournalEntryAccountDetails():
    frappe.clear_cache()
    return frappe.get_all("Journal Entry Account",fields=["*"])    


@frappe.whitelist(allow_guest=True)
def getAccountDetailsByJournalNo():
    try:
        frappe.clear_cache()
        data = frappe.request.get_data(as_text=True)

        print(f"getAccountDetailsByJournalNo data:{data}")

        json_data = json.loads(data)

        print(f"getAccountDetailsByJournalNo json_data:{json_data}")

        journalNo = json_data.get("journalNo")

        print(f"journalNo :{journalNo}")

        filters = {
                    "parent": journalNo
                    }

        return frappe.get_all("Journal Entry Account", filters=filters , fields=["*"])   

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAccountDetailsByJournalNo')
        return {'status': 'error', 'message': str(e)}    
   