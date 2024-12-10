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
        recp_entries = frappe.get_all("Receipt", filters={"parent": recp['name']}, fields=["*"])
        recp["receipt_entries"] = recp_entries

    return { 
        "receipt_information": recp_info
    }


@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoDetailsByExecutive(executive, amount=None, date=None, customer=None):
    try:
        filters = {}
        if executive and executive != 'All':
            filters["executive"] = executive
            if amount is not None:
                if float(amount) > 0:
                    filters["amount"] = amount
                elif float(amount) == 0:
                    pass  # No need to add amount filter if it's zero
            if date:
                filters["date"] = date
            if customer and customer != 'N/A':
                filters["custom_customer"] = customer

        # Construct the WHERE clause
        where_clause = "WHERE " + " AND ".join([f"{key}=%s" for key in filters.keys()]) if filters else ""

        # Fetch all relevant data in one query
        query = f"""
            SELECT DISTINCT *
            FROM `tabPayment Info`
            {where_clause}
        """
        recp_info = frappe.db.sql(query, tuple(filters.values()), as_dict=True)
        if not recp_info:
            recp_info = []

        # Add receipt entries to each receipt information record
        for recp in recp_info:
            query = f"""
            SELECT DISTINCT *
            FROM `tabReceipt`
            WHERE parent=%s
            """
            recp_entries = frappe.db.sql(query, (recp['name'],), as_dict=True)
            recp["receipt_entries"] = recp_entries    

        return recp_info

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoDetailsByExecutive')
        return {"status": "error", "message": str(e)}

   
@frappe.whitelist(allow_guest=True)
def getAllReceiptEntryDetails():
    recp_entry = frappe.get_all("Payment Info", fields=["*"])
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
        # Initialize the base SQL query
        filters = []
        
        # Apply filters conditionally
        if not int(all) and executive:
            filters.append(f"executive = {frappe.db.escape(executive)}")
        if deposit_date:
            filters.append(f"date = {frappe.db.escape(deposit_date)}")
        if deposit_amount:
            filters.append(f"amount = {frappe.db.escape(deposit_amount)}")
        
        # Construct the WHERE clause
        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Fetch all relevant data in one query
        query = f"""
            SELECT DISTINCT executive, date, amount,mode_of_payment	,custom_customer
            FROM `tabPayment Info`
           
        """
        results = frappe.db.sql(query, as_dict=True)

        # Process the results to extract unique executives, dates, and amounts
        unique_executives = sorted(set([row['executive'] for row in results if row['executive']])) or ['N/A']
        unique_dates = sorted(set([row['date'] for row in results if row['date']])) or ['N/A']
        unique_amounts = sorted(set([row['amount'] for row in results if row['amount']])) or ['N/A']
        unique_payment_mode = sorted(set([row['mode_of_payment'] for row in results if row['mode_of_payment']])) or ['N/A']
        unique_custom_customer = sorted(set([row['custom_customer'] for row in results if row['custom_customer']])) or ['N/A']

        return {
            "executives": unique_executives,
            "dates": unique_dates,
            "payment_mode": unique_payment_mode,
            "customer": unique_custom_customer,
            "amounts": unique_amounts
        }

    except Exception as e:
        # Log the error with traceback for debugging
        frappe.log_error(message=frappe.get_traceback(), title="Error fetching filter options")
        return {"error": "An error occurred while fetching filter options. Please try again later."}


