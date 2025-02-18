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

        # print(f"getAccountDetailsByJournalNo data:{data}")

        json_data = json.loads(data)

        # print(f"getAccountDetailsByJournalNo json_data:{json_data}")

        journalNo = json_data.get("journalNo")

        # print(f"journalNo :{journalNo}")

        filters = {
                    "parent": journalNo
                    }

        return frappe.get_all("Journal Entry Account", filters=filters , fields=["*"])   

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAccountDetailsByJournalNo')
        return {'status': 'error', 'message': str(e)}    
   


def create_journal_entry(posting_date, voucher_type, accounts, remarks=None):
    # Create a new Journal Entry document
    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": posting_date,
        "voucher_type": voucher_type,  # "Bank Entry", "Cash Entry", "Journal Entry", etc.
        "accounts": accounts,
        "user_remark": remarks or "Journal Entry created programmatically"
    })

    # Insert and submit the Journal Entry
    journal_entry.insert()
    journal_entry.submit()

    # Return the name of the created Journal Entry
    return journal_entry.name   