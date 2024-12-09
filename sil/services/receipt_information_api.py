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
                recp_info = frappe.get_all("Payment Info", filters={"executive": executive, "name": receipt_number,"date":selected_date,"amount":selected_amount}, fields=["*"])
            else:
                recp_info = frappe.get_all("Payment Info", filters={"executive": executive, "name": receipt_number,"date":selected_date}, fields=["*"])    
        else:
            if selected_amount != 0:
                recp_info = frappe.get_all("Payment Info", filters={"name": receipt_number,"date":selected_date,"amount":selected_amount}, fields=["*"])
            else:
                recp_info = frappe.get_all("Payment Info", filters={"name": receipt_number,"date":selected_date}, fields=["*"])    

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
    recp_info = frappe.get_all("Payment Info", fields=["*"])

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
    recp_info = frappe.get_all("Payment Info",filters={"name": receipt_number}, fields=["*"])

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


        receipt_entries = frappe.get_all("Payment Info", filters=filters, fields=["name","date","amount","mode_of_payment","chequereference_number","executive"]) or []
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
    recp_info = frappe.get_all("Payment Info", fields=["name","executive"])

    if not recp_info:
        recp_info = []

    return recp_info    


# @frappe.whitelist(allow_guest=True)
# def get_filter_options(all=0,executive=None,deposit_date=None,deposit_amount=None):
#     try:
#         # # If `all` is checked, fetch all unique values
#         # if int(all):  # Convert `all` to integer for boolean logic
#         #     executives = frappe.db.sql_list("SELECT DISTINCT(executive) FROM `tabPayment Info` WHERE executive IS NOT NULL ORDER BY date ASC")
#         #     dates = frappe.db.sql_list("SELECT DISTINCT(date) FROM `tabPayment Info` WHERE date IS NOT NULL ORDER BY date ASC")
#         #     amounts = frappe.db.sql_list("SELECT DISTINCT(amount) FROM `tabPayment Info` WHERE amount >0 ORDER BY amount ASC")
#         # else:
#         #     # If `all` is unchecked, fetch only the required subset (add any specific logic here)
#         #     executives = frappe.db.sql_list("SELECT DISTINCT(executive) FROM `tabPayment Info` WHERE executive IS NOT NULL ORDER BY date ASC")
#         #     dates = frappe.db.sql_list("SELECT DISTINCT(date) FROM `tabPayment Info` WHERE date >= CURDATE() ORDER BY date ASC")
#         #     amounts = frappe.db.sql_list("SELECT DISTINCT(amount) FROM `tabPayment Info` WHERE amount > 0 ORDER BY amount ASC")

#         if not int(all):
#             if executive:
#                 filters['executive'] = executive

#         if deposit_date:
#             filters['date'] = deposit_date
#         if deposit_amount:
#             filters['amount'] = deposit_amount


#         executives = frappe.get_all('Payment Info', filters=filters, pluck='executive')
#         dates = frappe.get_all('Payment Info', filters=filters, pluck='deposit_date')
#         amounts = frappe.get_all('Payment Info', filters=filters, pluck='deposit_amount')            
#         return {
#             "executives": executives,
#             "dates": dates,
#             "amounts": amounts
#         }
#     except Exception as e:
#         frappe.log_error(message=frappe.get_traceback(), title="Error fetching filter options")
#         return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_filter_options(all=0, executive=None, deposit_date=None, deposit_amount=None):
    try:
        filters = []  # Initialize the filters list for SQL query

        # Apply filters conditionally
        if not int(all) and executive:  # Use 'and' instead of 'AND'
            filters.append("executive = %s" % frappe.db.escape(executive))
        if deposit_date:
            filters.append("date = %s" % frappe.db.escape(deposit_date))
        if deposit_amount:
            filters.append("amount = %s" % frappe.db.escape(deposit_amount))

        # Construct the WHERE clause
        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Fetch unique values using SQL query
        executives = frappe.db.sql(f"""
            SELECT executive FROM `tabPayment Info`
            {where_clause}
        """, as_dict=True)

        dates = frappe.db.sql(f"""
            SELECT date FROM `tabPayment Info`
            {where_clause}
        """, as_dict=True)

        amounts = frappe.db.sql(f"""
            SELECT amount FROM `tabPayment Info`
            {where_clause}
        """, as_dict=True)

        print("executives:")
        print(executives)
        print("dates:")
        print(dates)
        print("amounts:")
        print(amounts)
        # Extract the values from the result set and sort them
        unique_executives = sorted([e['executive'] for e in executives])
        unique_dates = sorted([d['date'] for d in dates])
        unique_amounts = sorted([a['amount'] for a in amounts])

        return {
            "executives": unique_executives,
            "dates": unique_dates,
            "amounts": unique_amounts
        }

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Error fetching filter options")
        return {"error": str(e)}


