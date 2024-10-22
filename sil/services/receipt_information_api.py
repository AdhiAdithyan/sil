import frappe 
from frappe import _
import re


@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoByRefferenceType():
    try:
        frappe.clear_cache()
        data = frappe.request.get_data(as_text=True)

        print(f"getAllReceiptInfoByRefferenceType data:{data}")

        json_data = json.loads(data)

        refference_type = json_data.get("refference_type")
        cust_name = json_data.get("customer_name")


        if refference_type == "Sales Invoice":
            filters = {
                    "customer": cust_name
                    }
            return frappe.get_all("Sales Invoice", filters=filters , fields=["*"])   
        elif refference_type == "Sales Order":
            filters = {
                    "customer": cust_name
                    }
            return frappe.get_all("Sales Order", filters=filters , fields=["*"]) 
        elif refference_type == "Slip No": 
            filters = {
                    "customer": cust_name
                    }
            return frappe.get_all("Issue Sales", filters=filters , fields=["*"])    
        elif refference_type == "Advance": 
            filters = {
                    "customer": cust_name
                    }
            return frappe.get_all("Issue Sales", filters=filters , fields=["*"])  
        else:
            return {
                """
                Add validation error message here
                """
            }          


    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoByRefferenceType')
        return {'status': 'error', 'message': str(e)} 