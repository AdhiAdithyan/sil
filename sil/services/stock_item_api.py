import frappe
from frappe import _
import re
from bs4 import BeautifulSoup
from sil.services.utils import ensure_column_exists



@frappe.whitelist(allow_guest=True)
def getAllStockWithUploadStatus(data):
    try:
        # Clear the cache
        frappe.clear_cache()
        
        #Parse the JSON data
        data_dict=frappe.parse_json(data)
        #Extract the relevant data
        status=data_dict.get("Status")
        # Cast status to integer
        status = int(status)
        # ensure_column_exists("Item", "is_tally_updated", "Int")
        # for returning all the sales invoice details which are not updated in the tally application.
        return frappe.db.sql(f"""Select * from `tabItem` where is_tally_updated={status};""",as_dict=True)
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        return {"success": False, "message": f"An error occurred while processing the request.{e}"}  


@frappe.whitelist(allow_guest=True)
def getAllStock():
    try:
        # Clear the cache
        frappe.clear_cache()
        # for returning all the sales invoice details which are not updated in the tally application.
        return frappe.db.sql(f"""Select * from `tabItem` ;""",as_dict=True)
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        return {"success": False, "message": f"An error occurred while processing the request.{e}"}    



@frappe.whitelist(allow_guest=True)
def updateStockItemUploadStatus(data):
    try:
        # Clear the cache
        frappe.clear_cache()

        # Parse the JSON data
        data_dict = frappe.parse_json(data)
        
        # Extract the relevant data
        itemCode = data_dict.get("item_code")
        
        if itemCode:
            try:
                # Update the database record 
                sql_query = """UPDATE `tabItem` SET is_tally_updated = 1 WHERE item_code=%s """
                frappe.db.sql(sql_query, (itemCode,))
                
                # Commit the transaction
                frappe.db.commit()
                
                # Log successful update
                frappe.logger().info(f"Item with code {itemCode} updated successfully.")
                
                return {"success": True, "message": "Data updated successfully", "ItemCode": itemCode}   
            except Exception as e:
                # Log error
                frappe.logger().error(f"Error updating Item with code {itemCode}: {e}")
                
                return {"success": False, "message": f"An error occurred while processing the request: {str(e)}"}
        else:
            return {"success": False, "message": "item_code parameter is missing"}
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        
        return {"success": False, "message": f"An error occurred while processing the request.Error:{e}"}


