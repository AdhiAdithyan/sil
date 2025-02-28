import frappe

# @frappe.whitelist(allow_guest=True)
# def get_suspense_entries():
#     query = """
#     SELECT * FROM (
#         SELECT
#             name AS receipt_id,
#             amount_received AS amount,
#             executive,
#             date,
#             mode_of_payment,
#             COALESCE(reference_number, '') AS reference_number,
#             COALESCE(chequereference_date, '') AS reference_date
#         FROM `tabPayment Receipt`
#         WHERE
#             payment_type = 'Internal Transfer'
#             AND custom_status = 'Processing'
#             AND custom_is_suspense_entry = 1
#             AND docstatus = 1

#         UNION ALL

#         SELECT 
#             jo.parent AS receipt_id,
#             jo.credit AS amount,
#             '' AS executive,
#             jo.creation AS date,
#             '' AS mode_of_payment,
#             '' AS reference_number,
#             '' AS reference_date
#         FROM `tabJournal Entry Account` jo
#         INNER JOIN `tabAccount` ta ON jo.account = ta.name
#         WHERE  
#             jo.docstatus = 1
#             AND ta.custom_is_suspense = 1
#             AND jo.custom_is_apportion_done != 1
#             AND jo.debit = 0
#             AND jo.credit != 0
#     ) AS suspense_entries
#     ORDER BY date DESC;
#     """
    
#     # Execute the query and return the results as a list of dictionaries.
#     entries = frappe.db.sql(query, as_dict=True)
#     return entries

import frappe

import frappe

@frappe.whitelist(allow_guest=True)
def get_payment_entries():
    """
    Fetch all Payment Entry records where docstatus = 1 and nest their child entries
    from the Payment Entry Reference table as 'references'.

    Returns:
        dict: A dictionary containing the status and data or an error message.
    """
    try:
        # Fetch Payment Entry records with docstatus = 1
        query = """
            SELECT *
            FROM `tabPayment Entry`
            WHERE docstatus = 1
        """
        payment_entries = frappe.db.sql(query, as_dict=True)
        if not payment_entries:
            return {"status": "error", "message": "No payment entries found."}
        
        # Extract the unique names of Payment Entry records
        payment_entry_names = [entry["name"] for entry in payment_entries]
        
        # Build and execute query to fetch all child records from Payment Entry Reference
        placeholders = ','.join(['%s'] * len(payment_entry_names))
        child_query = f"""
            SELECT *
            FROM `tabPayment Entry Reference`
            WHERE parent IN ({placeholders})
        """
        child_entries = frappe.db.sql(child_query, tuple(payment_entry_names), as_dict=True)
        
        # Group child records by their parent Payment Entry
        child_dict = {}
        for child in child_entries:
            parent = child.get("parent")
            child_dict.setdefault(parent, []).append(child)
        
        # Nest the child records under the corresponding Payment Entry record
        for entry in payment_entries:
            entry["references"] = child_dict.get(entry["name"], [])
        
        return {"status": "success", "data": payment_entries}
    
    except Exception as e:
        frappe.log_error(message=str(e), title="get_payment_entries API Error")
        return {"status": "error", "message": f"An error occurred while fetching payment entries: {str(e)}"}


import frappe

@frappe.whitelist(allow_guest=True)
def get_journal_entries():
    """
    Fetch all Journal Entry records where docstatus = 1 and nest their child entries from 
    the Journal Entry Account table as 'accounts'.
    
    Returns:
        dict: A dictionary containing the status and data or an error message.
    """
    try:
        # Fetch Journal Entry records with docstatus = 1
        journal_query = """
            SELECT *
            FROM `tabJournal Entry`
            WHERE docstatus = 1
        """
        journal_entries = frappe.db.sql(journal_query, as_dict=True)
        if not journal_entries:
            return {"status": "error", "message": "No journal entries found."}
        
        # Get list of Journal Entry names to fetch corresponding child records
        journal_entry_names = [je["name"] for je in journal_entries]
        
        # Fetch all child records from Journal Entry Account where parent is in the list above
        placeholders = ','.join(['%s'] * len(journal_entry_names))
        child_query = f"""
            SELECT *
            FROM `tabJournal Entry Account`
            WHERE parent IN ({placeholders})
        """
        child_entries = frappe.db.sql(child_query, tuple(journal_entry_names), as_dict=True)
        
        # Group child records by parent
        child_dict = {}
        for child in child_entries:
            parent = child.get("parent")
            child_dict.setdefault(parent, []).append(child)
        
        # Nest the child records within the corresponding Journal Entry
        for je in journal_entries:
            je["accounts"] = child_dict.get(je["name"], [])
        
        return {"status": "success", "data": journal_entries}
    
    except Exception as e:
        frappe.log_error(message=str(e), title="get_journal_entries API Error")
        return {"status": "error", "message": f"An error occurred while fetching journal entries: {str(e)}"}


import frappe

@frappe.whitelist(allow_guest=True)
def update_payment_entry_tally_status(name=None):
    """
    Update the 'custom_is_tally_updated' field to 1 for a Payment Entry with the given name.

    Args:
        name (str): The unique name of the Payment Entry record.

    Returns:
        dict: A dictionary with the status and message of the update.
    """
    if not name:
        return {"status": "error", "message": "Parameter 'name' is required."}
    
    try:
        # Check if the record exists
        if not frappe.db.exists("Payment Entry", name):
            return {"status": "error", "message": f"Payment Entry with name '{name}' not found."}
        
        # Update the field to 1
        frappe.db.set_value("Payment Entry", name, "custom_is_tally_updated", 1)
        frappe.db.commit()
        
        return {"status": "success", "message": f"Payment Entry '{name}' updated successfully."}
    
    except Exception as e:
        frappe.log_error(message=str(e), title="update_payment_entry_tally_status API Error")
        return {"status": "error", "message": f"Error updating Payment Entry: {str(e)}"}

import frappe

@frappe.whitelist(allow_guest=True)
def update_journal_entry_tally_status(name=None):
    """
    Update the 'custom_is_tally_updated' field to 1 for a Journal Entry with the given name.

    Args:
        name (str): The unique name of the Journal Entry record.

    Returns:
        dict: A dictionary with the status and message of the update.
    """
    if not name:
        return {"status": "error", "message": "Parameter 'name' is required."}
    
    try:
        # Check if the record exists
        if not frappe.db.exists("Journal Entry", name):
            return {"status": "error", "message": f"Journal Entry with name '{name}' not found."}
        
        # Update the field to 1
        frappe.db.set_value("Journal Entry", name, "custom_is_tally_updated", 1)
        frappe.db.commit()
        
        return {"status": "success", "message": f"Journal Entry '{name}' updated successfully."}
    
    except Exception as e:
        frappe.log_error(message=str(e), title="update_journal_entry_tally_status API Error")
        return {"status": "error", "message": f"Error updating Journal Entry: {str(e)}"}
