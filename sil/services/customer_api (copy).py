import frappe
from frappe import _
import re
from bs4 import BeautifulSoup
from sil.services.utils import ensure_column_exists



@frappe.whitelist(allow_guest=True)
def getAllCustomerDetails():
    # Clear the cache
    frappe.clear_cache()

    ensure_column_exists("Customer", "custom_is_tallyupdated", "Int")
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
        # Cast status to integer
        status = int(status)
        #0 for new
        #1 for uploaded to Tally
        #2 for if any fields updated which are related to tally
        #3 for new feild added
        ensure_column_exists("Customer", "custom_is_tallyupdated", "Int")
        # for returning all the customer details which are not updated in the tally application.
        return frappe.db.sql(f"""SELECT TC.name,TC.creation,TC.docstatus,TC.idx,TC.customer_name,TC.customer_type,
        TC.customer_group,TC.territory,TC.gender,TC.default_currency,TC.is_internal_customer,TC.mobile_no,
        TC.email_id,TC.customer_primary_address,TC.tax_category,TC.pan,TC.gstin,TC.gst_category,
        TC.custom_customer_category,TC.custom_customer_location_type,TC.custom_clusterproduct,
        TC.custom_cluster_managerproduct,TC.custom_zonal_managerproduct,TC.custom_zonal_managerspares,
        TC.custom_zonal_managerconsumables,TC.custom_zonal_manageramc,TC.custom_regionproduct,TC.custom_regionspares,
        TC.custom_regionconsumables,TC.custom_regionamc,TC.custom_state,TC.custom_citytown,
        TC.custom_is_tallyupdated,TA.address_line1,TA.gst_state_number,custom_customer_sub_category FROM tabCustomer TC LEFT 
        OUTER JOIN tabAddress TA ON TC.name=TA.name WHERE TC.custom_is_tallyupdated={status};""",as_dict=True)
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
                sql_query = """UPDATE `tabCustomer` SET custom_is_tallyupdated = 1 WHERE name=%s """
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

