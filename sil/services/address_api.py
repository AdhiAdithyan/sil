import frappe
from frappe import _
import re
from bs4 import BeautifulSoup



@frappe.whitelist(allow_guest=True)
def getAllAddressDetails():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the Address details which are not updated in the tally application.
    return frappe.db.sql("""Select * from `tabAddress`;""",as_dict=True)


