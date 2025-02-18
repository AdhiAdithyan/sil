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



@frappe.whitelist()
def generateSerialNo(items_series, form_doc):
    items_series = frappe.parse_json(items_series)
    # frappe.logger().info("generateSeriesNo items_series request: %s" % items_series)
    # print("items_series")
    # print(items_series)
    serial_nos = {}
    current_year_month = get_current_year_month()
    # print(f"current_year_month:{current_year_month}")
    for item_index, itemDetails in items_series.items():
        # print("items_series")
        # print(items_series)
        # print("items_series.items()")
        # print(items_series.items())
        # print("itemDetails")
        # print(itemDetails)
        # print("item_index")
        # print(item_index)
        item_code = itemDetails["item_code"]
        itemQty = itemDetails["quantity"]

        try:
            length = len(itemDetails["serial_Nos"])
        except KeyError:
            length = 0

        if length < 5:

            item_family_details = frappe.get_all(
                "Item Family", 
                filters={"family_name": itemDetails["item_family"]},
                fields=["name", "family_name", "series_prefix", "last_serial_no","do_you_have_a_serial_no"]
            )
            # print(f"item_family_details:{str(item_family_details)}")
            if item_family_details:
                item_family = item_family_details[0]
                try:
                    qty = int(itemQty)
                except ValueError:
                    qty = 0    

                last_series=0
                try:
                    last_series = int(item_family["last_serial_no"])
                except Exception as e:
                    last_series=0    
                
                item_prefix = f"{current_year_month}{item_family['series_prefix']}"
                hasSerialNo = item_family["do_you_have_a_serial_no"]

                # print(f"item_prefix:{item_prefix}")
                # print(f"hasSerialNo:{hasSerialNo}")

                if hasSerialNo=="NO" or hasSerialNo=="No":
                    updated_last_series = pad_string_with_zeros(str(last_series + 1),15)
                    starting_serialNo = f"{updated_last_series}B"
                    itemDetails["serial_Nos"] = ''
                    serial_nos[item_index] = itemDetails
                else:
                    item_prefix_len=len(item_prefix)
                    updated_last_series = pad_string_with_zeros(str(last_series + 1),15-item_prefix_len)
                    starting_serialNo = f"{item_prefix}{updated_last_series}B"  

                    for i in range(qty):
                        current_count = (i + 1)
                        count = last_series + current_count
                        if hasSerialNo=="NO" or hasSerialNo=="No":
                            value=pad_string_with_zeros(str(count),15)
                        else:
                            value = pad_string_with_zeros(str(count),5)

                        itemCode = itemDetails["item_code"]
                        cust_name = itemDetails["customer"]
                        itemName = itemDetails["item_name"]
                        if hasSerialNo=="NO" or hasSerialNo=="No":
                            # Check for duplicate entry
                            duplicate_check = frappe.db.exists("Item Family Serial No List", {
                                "customer": cust_name,
                                "item_code": item_index,
                                "item_name": itemName,
                                "item_family": itemDetails["item_family"],
                                "serial_no": f"{value}B"
                            })
                        else:
                            # Check for duplicate entry
                            duplicate_check = frappe.db.exists("Item Family Serial No List", {
                                "customer": cust_name,
                                "item_code": item_index,
                                "item_name": itemName,
                                "item_family": itemDetails["item_family"],
                                "serial_no": f"{item_prefix}{value}B"
                            })

                        if duplicate_check:
                            frappe.logger().info(f"Duplicate entry detected: {duplicate_check}")
                            return {"success": False, "message": "Duplicate entry detected"}
                        else:
                            # Get current date and time as a string
                            current_time_str = now()
                            item_classification = frappe.db.get_value('Item', itemCode, 'custom_item_classification')

                            frappe.logger().info("Current Date String: %s" % current_time_str)
                            if hasSerialNo=="NO" or hasSerialNo=="No":
                                value=pad_string_with_zeros(str(value),15)
                                item_family_serial_no_list = {
                                "doctype": "Item Family Serial No List",
                                "customer": cust_name,
                                "item": itemCode,
                                "custom_item_classification":item_classification,
                                "custom_sales_order":itemDetails["sales_order_name"],
                                "item_name": itemName,
                                "item_family": itemDetails["item_family"],
                                "dateTime": current_time_str,
                                "serial_no": f"{value}B"
                                }
                            else:
                                item_prefix_len=len(item_prefix)
                                value=pad_string_with_zeros(str(value),15-item_prefix_len)

                                item_family_serial_no_list = {
                                "doctype": "Item Family Serial No List",
                                "customer": cust_name,
                                "item": itemCode,
                                "custom_item_classification":item_classification,
                                "custom_sales_order":itemDetails["sales_order_name"],
                                "item_name": itemName,
                                "item_family": itemDetails["item_family"],
                                "dateTime": current_time_str,
                                "serial_no": f"{item_prefix}{value}B"
                                }


                            frappe.logger().info("item_family_serial_no_list: %s" % item_family_serial_no_list)
                            
                            # Insert data into the database
                            frappe.get_doc(item_family_serial_no_list).insert(ignore_permissions=True)
                            

                            # Update the Item Family with the latest series number
                            frappe.db.sql(
                                    """UPDATE `tabItem Family` SET `last_serial_no` = %s WHERE `family_name`=%s;""",
                                    (value, itemDetails["item_family"])
                                )
                            
                        
                        try:
                            
                            
                            if hasSerialNo=="NO" or hasSerialNo=="No":
                                value=pad_string_with_zeros(str(last_series + 1),15)
                                if updated_last_series == value:
                                    current_serialNo = f"{updated_last_series}B"
                                else:
                                    current_serialNo = f"{updated_last_series}B - {value}B"    
                            else:
                                item_prefix_len=len(item_prefix)
                                value=pad_string_with_zeros(str(last_series + 1),15-item_prefix_len)
                                if updated_last_series == value:
                                    current_serialNo = f"{item_prefix}{updated_last_series}B"   
                                else:
                                    current_serialNo = f"{item_prefix}{updated_last_series}B - {item_prefix}{value}B"       


                            # Update the Item Series No with the new serial numbers
                            frappe.db.sql(
                                """UPDATE `tabItem Series No` SET `serial_nos` = %s WHERE `parent`=%s AND `item_series`=%s;""",
                                (current_serialNo, form_doc, itemName)
                            )
                            

                            frappe.logger().info(f"Serial {value} updated successfully.")
                        except Exception as e:
                            frappe.logger().error(f"Error updating order : {e}")
                            
                        if qty == current_count:
                            if hasSerialNo=="NO" or hasSerialNo=="No":
                                last_series=pad_string_with_zeros(str(last_series + qty),15)
                                starting_serialNo = f"{updated_last_series}B"
                                ending_serialNo = f"{last_series}B"
                                if updated_last_series == last_series:
                                    itemDetails["serial_Nos"] = f'{starting_serialNo}'
                                else:
                                    itemDetails["serial_Nos"] = f'{starting_serialNo} - {ending_serialNo}'    
                                # itemDetails["serial_Nos"] = f'{starting_serialNo} - {ending_serialNo}'    
                            else:
                                item_prefix_len=len(item_prefix)
                                last_series=pad_string_with_zeros(str(last_series + qty),15-item_prefix_len)
                                starting_serialNo = f"{item_prefix}{updated_last_series}B"
                                ending_serialNo = f"{item_prefix}{last_series}B"
                                if updated_last_series == last_series:
                                    itemDetails["serial_Nos"] = f'{starting_serialNo}'
                                else:
                                    itemDetails["serial_Nos"] = f'{starting_serialNo} - {ending_serialNo}'    
                                # itemDetails["serial_Nos"] = f'{starting_serialNo} - {ending_serialNo}'    
                            
                            # checking for warranty applicable items.
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
                                    "serial_no": itemDetails["serial_Nos"],
                                    "date":current_datetime
                                    # "serial_no": f"{item_prefix}{value}B"
                                }

                                frappe.logger().info("warranty_card_details: %s" % warranty_card_details)
                                
                                # Insert data into the database
                                frappe.get_doc(warranty_card_details).insert(ignore_permissions=True)
                                

                                # frappe.db.set_value("Item Family", item_family["name"], "last_serial_no", int(last_series) + qty)
                                # frappe.db.commit()
                                serial_nos[item_index] = itemDetails
            else:
                serial_nos[item_index] = None  # Handle cases where item family details are not found
                return {"success": False, "message": "Item family details missing...", "serial_nos": serial_nos}
        else:
            frappe.logger().info("Duplicate entry")
            serial_nos[item_index] = None
            return {"success": False, "message": "Duplicate entry", "serial_nos": serial_nos}

        frappe.db.commit()
    # print(f"serial_nos: {str(serial_nos)}")
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