import frappe
from frappe.utils import now
from frappe.model.document import Document
from frappe.utils import now_datetime
import datetime
import time
import logging

# Set up logging
logger = logging.getLogger(__name__)



@frappe.whitelist(allow_guest=True)
def getAllItemFamily():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the item family details
    return frappe.db.sql("""Select * from `tabItem Family`;""",as_dict=True)



@frappe.whitelist(allow_guest=True)
def getAllWarranty():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the item family details
    return frappe.db.sql("""Select * from `tabWarranty Card`;""",as_dict=True)



@frappe.whitelist(allow_guest=True)
def getAllItemFamilySerialNoList():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the item family details
    return frappe.db.sql("""Select * from `tabItem Family Serial No List`;""",as_dict=True)



@frappe.whitelist(allow_guest=True)
def getAllItemSeriesNoDetails():
    # Clear the cache
    frappe.clear_cache()

    # for returning all the item family details
    return frappe.db.sql("""Select * from `tabItem Series No`;""",as_dict=True)



@frappe.whitelist(allow_guest=True)
def getAllSalesOrderDetails():
    try:
        # sales_orders = frappe.get_all("Sales Order", fields=["name", "customer", "transaction_date", "status"])
        # return {"success": True, "data": sales_orders}
        return frappe.db.sql("""Select * from `tabSales Order`;""",as_dict=True)
    except Exception as e:
        frappe.logger().error(f"Error fetching sales order details: {e}")
        return {"success": False, "message": str(e)}

def pad_string_with_zeros(s, length=5):
    return s.zfill(length)


def pad_string_with_zeros(s, length):
    return s.zfill(length)


def convert_to_integer(input_string):
    try:
        input_string = input_string.strip()
        return int(input_string)
    except ValueError:
        raise ValueError("Invalid input: cannot convert to integer")


def append_zeros(input_string, default_size):
    return input_string.ljust(default_size, '0')



def get_current_year_month():
    now = datetime.datetime.now()
    year_month = now.strftime("%Y%m")
    return year_month



@frappe.whitelist(allow_guest=True)
def generateSerialNo(items_series, form_doc):
    items_series = frappe.parse_json(items_series)
    serial_nos = {}
    current_year_month = get_current_year_month()
    
    for item_index, itemDetails in items_series.items():
        item_code = itemDetails["item_code"]
        itemQty = itemDetails["quantity"]

        # Check if serial numbers already exist
        try:
            length = len(itemDetails["serial_nos"])
        except KeyError:
            length = 0

        if length < 5:
            # Begin transaction with FOR UPDATE lock to prevent race conditions
            try:
                # Lock the item family row for the duration of this transaction
                item_family = frappe.db.sql("""
                    SELECT name, family_name, series_prefix, last_serial_no, do_you_have_a_serial_no 
                    FROM `tabItem Family` 
                    WHERE family_name = %s
                    FOR UPDATE
                """, (itemDetails["item_family"],), as_dict=1)
                
                if not item_family:
                    serial_nos[item_index] = None
                    return {"success": False, "message": "Item family details missing...", "serial_nos": serial_nos}
                
                item_family = item_family[0]
                
                # Convert quantity to integer safely
                try:
                    qty = int(itemQty)
                except ValueError:
                    qty = 0
                
                # Convert last_serial_no to integer safely
                try:
                    last_series = int(item_family["last_serial_no"])
                except Exception:
                    last_series = 0
                
                item_prefix = f"{current_year_month}{item_family['series_prefix']}"
                hasSerialNo = item_family["do_you_have_a_serial_no"]
                
                # Process based on serial number configuration
                if hasSerialNo.upper() == "NO":
                    updated_last_series = pad_string_with_zeros(str(last_series + 1), 15)
                    starting_serialNo = f"{updated_last_series}B"
                    itemDetails["serial_nos"] = ''
                    serial_nos[item_index] = itemDetails
                else:
                    # Generate serial numbers with prefix
                    item_prefix_len = len(item_prefix)
                    updated_last_series = pad_string_with_zeros(str(last_series + 1), 15-item_prefix_len)
                    starting_serialNo = f"{item_prefix}{updated_last_series}B"
                    
                    # Create an array to store all serial numbers we'll generate
                    serial_numbers_to_create = []
                    
                    # Pre-generate all serial numbers
                    for i in range(qty):
                        current_count = (i + 1)
                        count = last_series + current_count
                        
                        if hasSerialNo.upper() == "NO":
                            value = pad_string_with_zeros(str(count), 15)
                            serial_number = f"{value}B"
                        else:
                            value = pad_string_with_zeros(str(count), 15-item_prefix_len)
                            serial_number = f"{item_prefix}{value}B"
                        
                        # Prepare data for serial number entry
                        cust_name = itemDetails["customer"]
                        itemCode = itemDetails["item_code"]
                        itemName = itemDetails["item_name"]
                        
                        # Check for duplicate entry
                        duplicate_check = frappe.db.exists("Item Family Serial No List", {
                            "customer": cust_name,
                            "item_code": itemCode,
                            "item_name": itemName,
                            "item_family": itemDetails["item_family"],
                            "serial_no": serial_number
                        })
                        
                        if duplicate_check:
                            frappe.logger().info(f"Duplicate entry detected: {duplicate_check}")
                            return {"success": False, "message": "Duplicate entry detected"}
                        
                        # Get current date and time
                        current_time_str = now()
                        item_classification = frappe.db.get_value('Item', itemCode, 'custom_item_classification')
                        
                        # Prepare serial number entry
                        item_family_serial_no_list = {
                            "doctype": "Item Family Serial No List",
                            "customer": cust_name,
                            "item": itemCode,
                            "custom_item_classification": item_classification,
                            "custom_sales_order": itemDetails["sales_order_name"],
                            "item_name": itemName,
                            "item_family": itemDetails["item_family"],
                            "dateTime": current_time_str,
                            "serial_no": serial_number
                        }
                        
                        serial_numbers_to_create.append(item_family_serial_no_list)
                        
                        # If we've processed all quantities, update the serial_nos in itemDetails
                        if qty == current_count:
                            if hasSerialNo.upper() == "NO":
                                last_series_str = pad_string_with_zeros(str(last_series + qty), 15)
                                ending_serialNo = f"{last_series_str}B"
                                
                                if updated_last_series == last_series_str:
                                    itemDetails["serial_nos"] = f'{starting_serialNo}'
                                else:
                                    itemDetails["serial_nos"] = f'{starting_serialNo} - {ending_serialNo}'
                            else:
                                last_series_str = pad_string_with_zeros(str(last_series + qty), 15-item_prefix_len)
                                ending_serialNo = f"{item_prefix}{last_series_str}B"
                                
                                if updated_last_series == last_series_str:
                                    itemDetails["serial_nos"] = f'{starting_serialNo}'
                                else:
                                    itemDetails["serial_nos"] = f'{starting_serialNo} - {ending_serialNo}'
                    
                    # Now insert all serial numbers at once
                    for entry in serial_numbers_to_create:
                        frappe.get_doc(entry).insert(ignore_permissions=True)
                    
                    # Update the Item Family with the latest series number - we're still in the lock
                    final_value = pad_string_with_zeros(str(last_series + qty), 15-item_prefix_len if hasSerialNo.upper() != "NO" else 15)
                    frappe.db.sql(
                        """UPDATE `tabItem Family` SET `last_serial_no` = %s WHERE `name`=%s;""",
                        (final_value, item_family["name"])
                    )
                    
                    # Update the Item Series No with the new serial numbers
                    try:
                        if hasSerialNo.upper() == "NO":
                            value = pad_string_with_zeros(str(last_series + qty), 15)
                            current_serialNo = itemDetails["serial_nos"]
                        else:
                            current_serialNo = itemDetails["serial_nos"]
                        
                        frappe.db.sql(
                            """UPDATE `tabItem Series No` SET `serial_no` = %s WHERE `parent`=%s AND `item_name`=%s;""",
                            (current_serialNo, form_doc, itemName)
                        )
                    except Exception as e:
                        frappe.logger().error(f"Error updating order: {e}")
                    
                    # Check if warranty is applicable and create warranty card
                    stock_check = frappe.db.exists("Item", {
                        "item_code": itemDetails["item_code"],
                        "custom_item_classification": "Finished Products"
                    })
                    
                    if stock_check:
                        current_datetime = now_datetime()
                        warranty_card_details = {
                            "doctype": "Warranty Card",
                            "customer": cust_name,
                            "item": itemCode,
                            "item_name": itemName,
                            "item_family": itemDetails["item_family"],
                            "dateTime": current_time_str,
                            "serial_no": itemDetails["serial_nos"],
                            "date": current_datetime
                        }
                        
                        frappe.logger().info("warranty_card_details: %s" % warranty_card_details)
                        frappe.get_doc(warranty_card_details).insert(ignore_permissions=True)
                    
                    # Store the result
                    serial_nos[item_index] = itemDetails
                
                # Commit the transaction to release the lock
                frappe.db.commit()
                
            except Exception as e:
                # Rollback in case of any error
                frappe.db.rollback()
                frappe.logger().error(f"Error generating serial number: {e}")
                return {"success": False, "message": f"Error generating serial number: {str(e)}", "serial_nos": serial_nos}
        else:
            frappe.logger().info("Serial numbers already exist")
            serial_nos[item_index] = itemDetails
    
    return {"success": True, "serial_nos": serial_nos}




@frappe.whitelist(allow_guest=True)
def getAllSalesOrder():
    try:
        sales_orders = frappe.db.sql("""
        SELECT * FROM `tabSales Order`;
    """, as_dict=True)
        return {"success": True, "data": sales_orders}
    except Exception as e:
        frappe.logger().error(f"Error fetching sales order details: {e}")
        return {"success": False, "message": str(e)}



@frappe.whitelist(allow_guest=True)
def saveGeneratedSerialNumber(doc):
    pass        

 
# @frappe.whitelist(allow_guest=True)
# def updateItemFamilySerialNoList(doc, method):
#     try:
#         frappe.clear_cache()

#         # Fetch sales order and parent from Sales Invoice Item table
#         sales_invoice_item = frappe.db.sql("""
#         SELECT DISTINCT sales_order, parent 
#         FROM `tabSales Invoice Item`
#         WHERE sales_order IS NOT NULL;""", as_dict=True)

#         # Loop through the sales invoice items and update the Item Family Serial No List
#         for record in sales_invoice_item:
#             sales_order = record['sales_order']
#             parent = record['parent']
#             print(f"Sales Order: {sales_order}, Parent: {parent}")

#             frappe.db.sql("""UPDATE `tabItem Family Serial No List` 
#             SET custom_sales_invoice=%s WHERE custom_sales_order=%s;""", 
#             (parent, sales_order), as_dict=True)

#         frappe.db.commit()
#         print(f"sales_invoice_item: {sales_invoice_item}")
#         return {"message": "success"}
#     except Exception as e:
#         print(str(e))
#         frappe.log_error(f"Error in updateItemFamilySerialNoList: {str(e)}")
#         return {"message": "failed", "error": str(e)}


@frappe.whitelist(allow_guest=True)
def updateItemFamilySerialNoList(doc, method):
    try:
        frappe.clear_cache()

        # Fetch sales order and parent from Sales Invoice Item table
        sales_invoice_items = frappe.db.sql("""
        SELECT DISTINCT sales_order, parent 
        FROM `tabSales Invoice Item`
        WHERE sales_order IS NOT NULL;""", as_dict=True)

        # Loop through the sales invoice items and update the Item Family Serial No List
        for record in sales_invoice_items:
            sales_order = record['sales_order']
            parent = record['parent']
            logger.info(f"Sales Order: {sales_order}, Parent: {parent}")

            # Update the Item Family Serial No List
            try:
                frappe.db.sql("""UPDATE `tabItem Family Serial No List` 
                SET custom_sales_invoice=%s WHERE custom_sales_order=%s;""", 
                (parent, sales_order))
            except Exception as update_error:
                logger.error(f"Failed to update for Sales Order: {sales_order}. Error: {str(update_error)}")

        frappe.db.commit()
        logger.info(f"Updated sales invoice items: {sales_invoice_items}")
        return {"message": "success"}
    except Exception as e:
        logger.error(f"Error in updateItemFamilySerialNoList: {str(e)}")
        return {"message": "failed", "error": str(e)}


@frappe.whitelist(allow_guest=True)
def getGrandTotalByOrderNumber(order_number):
    try:
        query = """
            SELECT DISTINCT 
                grand_total
            FROM `tabSales Order`
            WHERE 
                name=%s
        """
        # Pass the parameter to the query
        results = frappe.db.sql(query, (order_number,), as_dict=True)
        return results
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in getGrandTotalByOrderNumber")
        return {"error": str(e)}        