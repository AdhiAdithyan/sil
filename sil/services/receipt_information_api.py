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
            invoice = frappe.get_all("Sales Invoice", filters={"customer": customer,"docstatus":1,"outstanding_amount": [">", 0] }, fields=["name"])
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
            order = frappe.get_all("Sales Order", filters={"customer": customer,"docstatus":1}, fields=["name"])
            if order:
                response['reference_name'] = order
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Slip No":
            pass
            # Fetch the required fields from Issue Sales (Slip No equivalent)
            # slip = frappe.get_all("Issue", filters={"customer": customer,"docstatus":0}, fields=["name"])
            # if slip:
            #     response['reference_name'] = slip
            #     response['outstanding_amount'] = 0.0
            #     response['allocated_amount'] = 0.0
            # else:
            #     response['reference_name'] = None
            #     response['outstanding_amount'] = 0.0
            #     response['allocated_amount'] = 0.0

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
            invoice = frappe.get_all(
                                    "Sales Invoice",
                                    filters={
                                        "customer": customer,
                                        "name": reference_name,
                                        "outstanding_amount": [">", 0]  # Add condition for outstanding_amount > 0
                                    },
                                    fields=["name", "outstanding_amount", "due_date"]
                                )
            if invoice:
                response['outstanding_amount'] = invoice[0].get('outstanding_amount')
                response['allocated_amount'] = 0.0
            else:
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Sales Order":
            # Fetch the required fields from Sales Order
            order = frappe.get_all("Sales Order", filters={"customer": customer,"name":reference_name}, fields=["name", "grand_total", "delivery_date"])
            sales_orders = frappe.db.sql("""SELECT (rounded_total-advance_paid) as outstanding_amount FROM `tabSales Order` 
             where customer=%s and name=%s """,(customer,reference_name,), as_dict=True)
            # print("get_all_receipt_info_by_reference_name")
            # print(f"sales_orders :{sales_orders}")
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
    recp_info = frappe.get_all("Payment Intimation", fields=["*"])

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
                recp_info = frappe.get_all("Payment Intimation", filters={"executive": executive, "name": receipt_number,"date":selected_date,"amount":selected_amount,"custom_status":"Pending","custom_receipt_status":"Pending"}, fields=["*"])
            else:
                recp_info = frappe.get_all("Payment Intimation", filters={"executive": executive, "name": receipt_number,"date":selected_date,"custom_status":"Pending","custom_receipt_status":"Pending"}, fields=["*"])    
        else:
            if selected_amount != 0:
                recp_info = frappe.get_all("Payment Intimation", filters={"name": receipt_number,"date":selected_date,"amount":selected_amount,"custom_status":"Pending","custom_receipt_status":"Pending"}, fields=["*"])
            else:
                recp_info = frappe.get_all("Payment Intimation", filters={"name": receipt_number,"date":selected_date,"custom_status":"Pending","custom_receipt_status":"Pending"}, fields=["*"])    

        # If no records found, initialize as an empty list
        if not recp_info:
            recp_info = []

        # Add receipt entries to each receipt information record
        for recp in recp_info:
            recp_entries = frappe.get_all("Receipt", filters={"parent": recp['name']}, fields=["*"])
            recp["receipt_entries"] = recp_entries

        return recp_info

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoByExecutiveAndReceiptNo')
        return {"status": "error", "message": str(e)}
 
 

@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoDetails():
    recp_info = frappe.get_all("Payment Intimation", fields=["*"])

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
def getAllReceiptInfoDetailsByReceiptNo(receipt_number):
    try:
        recp_info = frappe.get_all("Payment Intimation",filters={"name": receipt_number}, fields=["*"])

        if not recp_info:
            recp_info = []

        # Add receipt entries to each receipt information record
        for recp in recp_info:
            try:
                recp_entries = frappe.get_all("Receipt", filters={"parent": recp['name']}, fields=["*"])
                recp["receipt_entries"] = sorted(recp_entries, key=lambda x: x.get("idx", 0))  # Default to 0 if 'idx' is missing
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoDetailsByReceiptNo')

        # print("receipt_information:123")
        # print(recp_info)

        return { 
            "receipt_information": recp_info
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoDetailsByReceiptNo')
        return {"status": "error", "message": str(e)} 


@frappe.whitelist(allow_guest=True)
def getAllReceiptInfoDetailsByExecutive(executive, amount=None, date=None, deposited_by=None,mode_of_payment=None):
    try:
        filters={}
        if executive and executive != 'All':
            filters["executive"] = executive
        
        if amount is not None:
            if float(amount) > 0:
                filters["amount"] = str(amount)
            elif float(amount) == 0:
                pass  # No need to add amount filter if it's zero
        if date:
            filters["date"] = date
        if mode_of_payment:
            filters["mode_of_payment"] = mode_of_payment    
        if deposited_by and deposited_by != 'N/A':
            filters["custom_customer"] = deposited_by

        filters["custom_status"] = 'Pending'
        filters["custom_receipt_status"] = 'Pending'

       

        # print("filters:::")
        # print(filters)
        # Construct the WHERE clause
        where_clause = "WHERE " + " AND ".join([f"{key}=%s" for key in filters.keys()]) if filters else ""

        # print("where_clause:::")
        # print(where_clause)
        # Fetch all relevant data in one query
        query = f"""
                SELECT DISTINCT *
                FROM `tabPayment Intimation`
                {where_clause}
                ORDER BY modified DESC
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
            ORDER BY idx ASC
            """
            recp_entries = frappe.db.sql(query, (recp['name'],), as_dict=True)
            recp["receipt_entries"] = recp_entries    

        return recp_info

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in getAllReceiptInfoDetailsByExecutive')
        return {"status": "error", "message": str(e)}

   
@frappe.whitelist(allow_guest=True)
def getAllReceiptEntryDetails():
    recp_entry = frappe.get_all("Payment Intimation", fields=["*"])
    if not recp_entry:
        recp_entry=[]

    return { 
        "receipt_entry" : recp_entry
    }  


@frappe.whitelist(allow_guest=True)
def getAllExecutivesAndReceipts():
    recp_info = frappe.get_all("Payment Intimation", fields=["name","executive"])

    if not recp_info:
        recp_info = []

    return recp_info    


@frappe.whitelist(allow_guest=True)
def get_filter_options(all=0, executive=None, deposit_date=None, deposit_amount=None,payment_mode=None,customer=None):
    try:
        # Initialize the base SQL query
        filters = []
        
        # Apply filters conditionally
        if not int(all) and executive:
            filters.append(f"executive = '{frappe.db.escape(executive)}'")
        if deposit_date:
            filters.append(f"date = '{frappe.db.escape(deposit_date)}'")
        if deposit_amount:
            filters.append(f"amount = {frappe.db.escape(deposit_amount)}")
        if payment_mode:
            filters.append(f"mode_of_payment = {frappe.db.escape(payment_mode)}") 
        if payment_mode:
            filters.append(f"custom_customer = {frappe.db.escape(customer)}")        
        
        filters.append(f"custom_status = {frappe.db.escape('Pending')}")  
        filters.append(f"custom_receipt_status = {frappe.db.escape('Pending')}")  
        # Construct the WHERE clause
        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Fetch all relevant data in one query
        query = f"""
            SELECT DISTINCT executive, date, amount,mode_of_payment,custom_customer
            FROM `tabPayment Intimation`
            {where_clause}
        """
        results = frappe.db.sql(query, as_dict=True)

        # Process the results to extract unique executives, dates, and amounts
        unique_executives = sorted(set([row['executive'] for row in results if row['executive']])) or ['N/A']
        unique_dates = sorted(set([row['date'] for row in results if row['date']])) or ['N/A']
        unique_amounts = sorted(set([row['amount'] for row in results if row['amount']])) or ['N/A']
        unique_payment_mode = sorted(set([row['mode_of_payment'] for row in results if row['mode_of_payment']])) or ['N/A']
        unique_custom_customer = sorted(set([row['custom_customer'] for row in results if row['custom_customer']])) or ['N/A']

        return {
            "executives": ['']+unique_executives,
            "dates": ['']+unique_dates,
            "payment_mode": ['']+unique_payment_mode,
            "customer": ['']+unique_custom_customer,
            "amounts": ['']+unique_amounts
        }

    except Exception as e:
        # Log the error with traceback for debugging
        frappe.log_error(message=frappe.get_traceback(), title="Error fetching filter options")
        return {"error": "An error occurred while fetching filter options. Please try again later."}


