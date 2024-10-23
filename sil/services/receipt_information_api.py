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
            slip = frappe.get_all("Issue Sales", filters={"customer": customer}, fields=["slip_no", "total_amount"])
            if slip:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0

        elif reference_type == "Advance":
            # Fetch the required fields from Advance Payments (or Issue Sales, depending on your structure)
            advance = frappe.get_all("Issue Sales", filters={"customer": customer}, fields=["name", "advance_amount"])
            if advance:
                response['reference_name'] = None
                response['outstanding_amount'] = 0.0
                response['allocated_amount'] = 0.0
            else:
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
            slip=frappe.db.sql("""SELECT *  FROM `tabIssue` where 
                `customer`=%s order by name asc;""",(customer,), as_dict=True)
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
