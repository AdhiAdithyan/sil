import frappe
from frappe import _
import re
from bs4 import BeautifulSoup
# from sil.services.utils import ensure_column_exists
   
   
@frappe.whitelist()
def get_custom_clusters(state_province):
    try:
        # Clear the cache
        frappe.clear_cache()

        # Execute the SQL query with parameter binding to prevent SQL injection
        query = """
            SELECT parent 
            FROM `tabStates` 
            WHERE state = %s 
            AND parenttype = 'Cluster Manager'
        """
        clusters = frappe.db.sql(query, (state_province,), as_dict=True)
        return clusters

    except Exception as e:
        # Log error
        frappe.logger().error(f"Error executing SQL query: {e}")
        return {"success": False, "message": f"An error occurred while processing the request: {e}"}



@frappe.whitelist(allow_guest=True)
def getAllClusterDetails():
    # Clear the cache
    frappe.clear_cache()

    # ensure_column_exists("Cluster", "is_tallyupdated", "Int")
    # for returning all the cluster details which are not updated in the tally application.
    return frappe.db.sql("""Select * from `tabCluster`;""",as_dict=True)


@frappe.whitelist(allow_guest=True)
def getAllClustWithStatus(data):
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
        # ensure_column_exists("Cluster", "is_tallyupdated", "Int")
        # for returning all the cluster details which are not updated in the tally application.
        return frappe.db.sql(f"""SELECT FROM tabCluster WHERE `is_tally_updated`={status};""", as_dict=True)
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        return {"success": False, "message": f"An error occurred while processing the request.{e}"}    




@frappe.whitelist(allow_guest=True)
def updateClusterStatus(data):
    try:
        # Clear the cache
        frappe.clear_cache()

        # Parse the JSON data
        data_dict = frappe.parse_json(data)
        
        # Extract the relevant data
        clusterName = data_dict.get("cluster_name")
        
        if clusterName:
            try:
                # Update the database record 
                sql_query = """UPDATE `tabCluster` SET is_tallyupdated = 1 WHERE name=%s """
                frappe.db.sql(sql_query, (clusterName,))
                
                # Commit the transaction
                frappe.db.commit()
                
                # Log successful update
                frappe.logger().info(f"Customer {clusterName} updated successfully.")
                
                return {"success": True, "message": "Data updated successfully", "Cluster": clusterName}   
            except Exception as e:
                # Log error
                frappe.logger().error(f"Error updating customer {custName}: {e}")
                
                return {"success": False, "message": f"An error occurred while processing the request: {str(e)}"}
        else:
            return {"success": False, "message": "cluster_name parameter is missing"}
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error parsing JSON data: {e}")
        
        return {"success": False, "message": "An error occurred while processing the request"}




