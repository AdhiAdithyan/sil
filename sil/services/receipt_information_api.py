import frappe
from frappe import _

@frappe.whitelist()
def get_all_receipt_info_by_reference_type_and_cust_name(customer, reference_type):
    try:
        # Log the inputs for debugging
        frappe.logger().info(f"Customer: {customer}, Reference Type: {reference_type}")

        # Initialize response dictionary
        response = {}

        # Logic for handling different reference types
        if reference_type == "Sales Invoice":
            # Fetch the required fields from Sales Invoice
            invoice = frappe.get_all("Sales Invoice", filters={"customer": customer}, fields=["name"])
            if invoice:
                response['reference_name'] = invoice
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Sales Order":
            # Fetch the required fields from Sales Order
            order = frappe.get_all("Sales Order", filters={"customer": customer}, fields=["name"])
            if order:
                response['reference_name'] = order
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Slip No":
            # Fetch the required fields from Issue Sales (Slip No equivalent)
            slip = frappe.get_all("Issue", filters={"customer": customer}, fields=["name"])
            if slip:
                response['reference_name'] = slip
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Advance":
            # Fetch the required fields from Advance Payments (or Issue Sales, depending on your structure)
            response['reference_name'] = None
            response['outstanding_amount'] = 0.0
            response['allocated_amount'] = 0.0

        else:
            frappe.throw(_("Invalid Reference Type"))

        # Log the response for debugging
        frappe.logger().info(f"Response: {response}")

        # Return the response to the client-side
        return response

    except Exception as e:
        # Log the error and return it as a message
        frappe.log_error(frappe.get_traceback(), 'Error in get_item_details')
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_all_receipt_info_by_reference_name(customer, reference_type,reference_name):
    try:
        # Log the inputs for debugging
        frappe.logger().info(f"Customer: {customer}, Reference Type: {reference_type},Refference Name:{reference_name}")

        # Initialize response dictionary
        response = {}

        # Logic for handling different reference types
        if reference_type == "Sales Invoice":
            # Fetch the required fields from Sales Invoice
            invoice = frappe.get_all("Sales Invoice", filters={"customer": customer,"name":reference_name}, fields=["name", "total", "due_date"])
            if invoice:
                response['outstanding_amount'] = invoice[0].get('total')
                response['allocated_amount'] = 0.0
            else:
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Sales Order":
            # Fetch the required fields from Sales Order
            order = frappe.get_all("Sales Order", filters={"customer": customer,"name":reference_name}, fields=["name", "grand_total", "delivery_date"])
            sales_orders = frappe.db.sql("""SELECT (rounded_total-advance_paid) as outstanding_amount FROM `tabSales Order` 
             where customer=%s and name=%s """,(customer,reference_name,), as_dict=True)
            print("get_all_receipt_info_by_reference_name")
            print(f"sales_orders :{sales_orders}")
            if sales_orders:
                response['outstanding_amount'] = sales_orders[0].get('outstanding_amount')
                response['allocated_amount'] = 0.0
            else:
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Slip No":
            # Fetch the required fields from Issue Sales (Slip No equivalent)
            # slip = frappe.get_all("Issue", filters={"customer": customer,"name":reference_name}, fields=["slip_no", "total_amount"])
            slip=frappe.db.sql("""SELECT *  FROM `tabIssue` where name=%s and `customer`=%s 
            order by name asc;""",(reference_name,customer,), as_dict=True)
            if slip:
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Advance":
            # Fetch the required fields from Advance Payments (or Issue Sales, depending on your structure)
            response['outstanding_amount'] = 0.0
            response['allocated_amount'] = 0.0

        else:
            frappe.throw(_("Invalid Reference Type"))

        # Log the response for debugging
        frappe.logger().info(f"Response: {response}")

        # Return the response to the client-side
        return response

    except Exception as e:
        # Log the error and return it as a message
        frappe.log_error(frappe.get_traceback(), 'Error in get_item_details')
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def getAllReceiptInfo():
    recp_info = frappe.get_all("Receipt Information", fields=["*"])

    if not recp_info:
        recp_info = []

    return recp_info



@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoByExecutiveAndReceiptNo(executive=None, receipt_number=None,selected_date=None,selected_amount=None):
    # Validate input parameters
    if not receipt_number:
        frappe.throw(_("Receipt number is required."))
    if executive is None:
        frappe.throw(_("Executive is required."))
    if selected_date is None:
        frappe.throw(_("selected_date is required.")) 
    if selected_amount is None:
        selected_amount = 0

    try:
        # Filter by executive and receipt number based on executive input
        if executive and executive != 'All':
            if selected_amount != 0:
                recp_info = frappe.get_all("Receipt Information", filters={"executive": executive, "name": receipt_number,"date":selected_date,"amount":selected_amount}, fields=["*"])
            else:
                recp_info = frappe.get_all("Receipt Information", filters={"executive": executive, "name": receipt_number,"date":selected_date}, fields=["*"])    
        else:
            if selected_amount != 0:
                recp_info = frappe.get_all("Receipt Information", filters={"name": receipt_number,"date":selected_date,"amount":selected_amount}, fields=["*"])
            else:
                recp_info = frappe.get_all("Receipt Information", filters={"name": receipt_number,"date":selected_date}, fields=["*"])    

        # If no records found, initialize as an empty list
        if not recp_info:
            recp_info = []

        # Add receipt entries to each receipt information record
        for recp in recp_info:
            recp_entries = frappe.get_all("Receipt Entry", filters={"parent": recp['name']}, fields=["*"])
            recp["receipt_entries"] = recp_entries

        return recp_info

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoByExecutiveAndReceiptNo')
        return {"status": "error", "message": str(e)}
 
 

@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoDetails():
    recp_info = frappe.get_all("Receipt Information", fields=["*"])

    if not recp_info:
        recp_info = []

    # Add receipt entries to each receipt information record
    for recp in recp_info:
        recp_entries = frappe.get_all("Receipt Entry", filters={"parent": recp['name']}, fields=["*"])
        recp["receipt_entries"] = recp_entries

    return { 
        "receipt_information": recp_info
    }


@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoDetailsByReceiptNo(receipt_number):
    recp_info = frappe.get_all("Receipt Information",filters={"name": receipt_number}, fields=["*"])

    if not recp_info:
        recp_info = []

    # Add receipt entries to each receipt information record
    for recp in recp_info:
        recp_entries = frappe.get_all("Receipt Entry", filters={"parent": recp['name']}, fields=["*"])
        recp["receipt_entries"] = recp_entries

    return { 
        "receipt_information": recp_info
    }


@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoDetailsByExecutive(executive,amount=None,date=None):
    try:
        if executive and executive != 'All' and float(amount)>0 and date !='':
            filters = {"executive": executive,"amount":amount,"date":date}
        elif executive and executive != 'All' and float(amount)>0 and date =='':
            filters = {"executive": executive,"amount":amount}
        elif executive and executive != 'All' and float(amount==0) and date =='':
            filters = {"executive": executive}         
        else:
            filters = {}    


        receipt_entries = frappe.get_all("Receipt Information", filters=filters, fields=["name","date","amount"]) or []
        return receipt_entries

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoDetailsByExecutive')
        return {"status": "error", "message": str(e)}

   
@frappe.whitelist(allow_guest=True)
def getAllReceiptEntryDetails():
    recp_entry = frappe.get_all("Receipt Entry", fields=["*"])
    if not recp_entry:
        recp_entry=[]

    return { 
        "receipt_entry" : recp_entry
    }  


@frappe.whitelist(allow_guest=True)
def getAllExecutivesAndReceipts():
    recp_info = frappe.get_all("Receipt Information", fields=["name","executive"])

    if not recp_info:
        recp_info = []

    return recp_info    