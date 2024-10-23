import frappe
from frappe import _
import re
import json
from bs4 import BeautifulSoup


@frappe.whitelist(allow_guest=True)
def getAllIssueSales():
    frappe.clear_cache()
    # Fetch all addresses linked to the given customer
    issue_history = frappe.get_all("Issue",fields=["*"])

    return issue_history


@frappe.whitelist(allow_guest=True)
def getAllServiceHistoryBySerialNo(serial_no):
    frappe.clear_cache()
    # Fetch all addresses linked to the given customer
    issue_history = frappe.get_all("Issue",
        filters={
            "custom_item_serial_no": serial_no
        },
        fields=["name", "customer","customer_name", "opening_date", "opening_time", 
        "custom_item_serial_no","custom_item_group", "custom_item",
        "custom_item_name","custom_complaint"
        ]
    )

    return issue_history


@frappe.whitelist(allow_guest=True)
def getAllServiceHistory():
    # Clearing cache might not be necessary unless required for specific reasons
    frappe.clear_cache()

    service_history=frappe.db.sql("""SELECT *  FROM `tabService History`;""",
    as_dict=True)

    return { 
        "service_history" : service_history
    } 


@frappe.whitelist(allow_guest=True)
def getIssueHistory(slip_no):
    # Clearing cache might not be necessary unless required for specific reasons
    frappe.clear_cache()

    service_history=frappe.db.sql("""SELECT *  FROM `tabIssue` where 
    `custom_item_serial_no`=%s order by name asc;""",(slip_no,), as_dict=True)

    if not service_history:
        service_history=[]

    return { 
        "service_history" : service_history
    }     


@frappe.whitelist(allow_guest=True)
def getAllIssuePaymentDetails():
    # Clearing cache might not be necessary unless required for specific reasons
    frappe.clear_cache()

    issue_payment=frappe.db.sql("""SELECT *  FROM `tabIssue Payment`;""",
    as_dict=True)

    if not issue_payment:
        issue_payment=[]

    return { 
        "issue_payment" : issue_payment
    } 


@frappe.whitelist(allow_guest=True)
def getAllIssuePriorityDetails():
    # Clearing cache might not be necessary unless required for specific reasons
    frappe.clear_cache()

    issue_priority = frappe.db.sql("""SELECT *  FROM `tabIssue Priority`;""",
    as_dict=True)

    return { 
        "issue_priority" : issue_priority
    } 




