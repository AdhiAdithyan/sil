import frappe
from frappe import _
import re
import json
from bs4 import BeautifulSoup


@frappe.whitelist(allow_guest=True)
def getAllCustomerDetails():
    # Clear the cache
    frappe.clear_cache()

    # ensure_column_exists("Customer", "custom_is_tallyupdated", "Int")
    # for returning all the customer details which are not updated in the tally application.
    return frappe.db.sql("""Select * from `tabCustomer`;""",as_dict=True)


@frappe.whitelist(allow_guest=True)
def getAllCustWithStatus(data):
    try:
        # Clear the cache
        frappe.clear_cache()

        #Parse the JSON data
        data_dict=frappe.parse_json(data)
        #Extract the relevant data
        status=data_dict.get("Status")
        CompanyName=data_dict.get("CompanyName")
        # Cast status to integer
        status = int(status)
        #0 for new
        #1 for uploaded to Tally
        #2 for if any fields updated which are related to tally
        #3 for new feild added
        # ensure_column_exists("Customer", "is_tally_updated", "Int")
        # for returning all the sales invoice details which are not updated in the tally application.
        return frappe.db.sql(f"""SELECT TC.name,TC.creation,TC.docstatus,TC.idx,TC.customer_name,TC.customer_type,
        TC.customer_group,TC.territory,TC.gender,TC.default_currency,TC.is_internal_customer,TC.mobile_no,
        TC.email_id,TC.customer_primary_address,TC.tax_category,TC.pan,TC.gstin,TC.gst_category,
        TC.custom_customer_category,TC.custom_customer_location_type,
        TC.custom_state,TC.custom_city_or_town,
        TC.is_tallyupdated AS custom_is_tallyupdated,TA.address_line1,TA.gst_state_number,custom_customer_sub_category FROM tabCustomer TC LEFT 
        OUTER JOIN tabAddress TA ON TC.name=TA.name WHERE TC.is_tallyupdated={status};""",as_dict=True)
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        return {"success": False, "message": f"An error occurred while processing the request.{e}"}    




@frappe.whitelist(allow_guest=True)
def updateCustomerUploadStatus(data):
    try:
        # Clear the cache
        frappe.clear_cache()

        # Parse the JSON data
        data_dict = frappe.parse_json(data)
        
        # Extract the relevant data
        custName = data_dict.get("cust_name")
        
        if custName:
            try:
                # Update the database record 
                sql_query = """UPDATE `tabCustomer` SET is_tallyupdated = 1 WHERE name=%s """
                frappe.db.sql(sql_query, (custName,))
                
                # Commit the transaction
                frappe.db.commit()
                
                # Log successful update
                frappe.logger().info(f"Customer {custName} updated successfully.")
                
                return {"success": True, "message": "Data updated successfully", "Customer": custName}   
            except Exception as e:
                # Log error
                frappe.logger().error(f"Error updating customer {custName}: {e}")
                
                return {"success": False, "message": f"An error occurred while processing the request: {str(e)}"}
        else:
            return {"success": False, "message": "cust_name parameter is missing"}
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        
        return {"success": False, "message": "An error occurred while processing the request"}


@frappe.whitelist(allow_guest=True)
def getAllCustDetails():
    try:
        # Clear the cache
        frappe.clear_cache()
        data = frappe.request.get_data(as_text=True)
        json_data = json.loads(data)

        starting_text = json_data.get("CustomerName")

        # for returning all the customer details which are not updated in the tally application.
        return frappe.db.sql(f"""SELECT TC.name as CustomerCode,TC.creation,TC.docstatus,TC.idx as CustomerID,TC.customer_name as CustomerName,TC.customer_type,
            TC.customer_group,TC.territory as Country,TC.gender,TC.default_currency,TC.is_internal_customer,TC.mobile_no,
            TC.email_id,TC.customer_primary_address,TC.tax_category,TC.pan,TC.gstin,TC.gst_category,
            TC.custom_customer_category,TC.custom_customer_location_type,TC.custom_clusterproduct,
            TC.custom_cluster_managerproduct,TC.custom_zonal_managerproduct,TC.custom_zonal_managerspares,
            TC.custom_zonal_managerconsumables,TC.custom_zonal_manageramc,TC.custom_regionspares,
            TC.custom_regionconsumables,TC.custom_regionamc,TC.custom_state as State,TC.custom_citytown as City,'' as Msg,0 as Status,0 as CreatedBy,
            TC.custom_is_tallyupdated,TA.address_line1,TA.gst_state_number,custom_customer_sub_category FROM tabCustomer TC LEFT 
            OUTER JOIN tabAddress TA ON TC.name=TA.name WHERE TC.customer_name LIKE %s LIMIT 10;""",(starting_text+'%',),as_dict=True)

    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        return {"success": False, "message": "An error occurred while processing the request"}       


@frappe.whitelist(allow_guest=True)
def getCustomerBySerialNo(serial_no):
    # Clearing cache might not be necessary unless required for specific reasons
    frappe.clear_cache()

    customer=frappe.db.sql("""
        SELECT it.*,tit.item_name as itemName,tit.item_group as item_group
        FROM `tabItem Family Serial No List` it
        LEFT OUTER JOIN `tabAddress` ta ON ta.address_title = it.customer
        LEFT OUTER JOIN `tabItem` tit ON tit.name = it.item
        WHERE it.name = %s; """, (serial_no,), as_dict=True)

    # Access the child table 'linked_with' (replace with your actual child table field name)
    linked_with_table = get_linked_addresses(customer[0]['customer'])

    issue_history = getIssueList(serial_no)

    # SQL query with corrected joins
    # print(f"linked_with_table:{linked_with_table}")
    # print(f"getCustomerBySerialNo customer:{customer}")
    # print(f"getCustomerBySerialNo issue:{issue_history}")

    return {
        "cust_name":customer[0]['customer'],
        "item":customer[0]['item'],
        "item_name":customer[0]['itemName'],
        "item_family":customer[0]['item_group'],
        "warranty_start":customer[0]['custom_warranty_start'],
        "warranty_expiry":customer[0]['custom_warranty_expiry'],
        "item_classification":customer[0]['custom_item_classification'],
        "sales_invoice":customer[0]['custom_sales_invoice'],
        "sales_order":customer[0]['custom_sales_order'],
        "issue_history":issue_history,
        "address":linked_with_table }


def get_linked_addresses(customer_name):
    frappe.clear_cache()
    # Fetch all addresses linked to the given customer
    linked_addresses = frappe.get_all("Address",
        filters={
            "link_doctype": "Customer",
            "link_name": customer_name
        },
        fields=["name", "address_line1", "address_line2", "city", "state", "pincode", "country"]
    )
    
    return linked_addresses


def getIssueList(serial_no):
    frappe.clear_cache()
    # Fetch all addresses linked to the given customer
    linked_Issue = frappe.get_all("Issue",
        filters={
            "custom_item_serial_no": serial_no
        },
        fields=["name", "opening_date","opening_time", "custom_item_serial_no", "custom_complaint",
         "custom_payment_status", "custom_partly_paid_amount", 
         "custom_payment_terms","custom_item_group","subject","status","issue_type"]
    )
    
    # print(f"linked_Issue:{linked_Issue}")
    return linked_Issue    


@frappe.whitelist()
def get_customer_addresses(customer_name):
    # Fetch billing and shipping addresses based on the customer_name
    billing_address_list = frappe.get_all("Address", filters={
            "link_doctype": "Customer",
            "link_name": customer_name
        }, fields=["name", "address_line1", "city", "state", "pincode", "country"])
    shipping_address_list = frappe.get_all("Address", filters={ "link_doctype": "Customer",
            "link_name": customer_name}, 
            fields=["name", "address_line1", "city", "state", "pincode", "country"])

    return {
        "billing_address_list": billing_address_list,
        "shipping_address_list": shipping_address_list
    }

