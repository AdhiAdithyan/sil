import frappe
from io import BytesIO
from openpyxl import Workbook
from frappe import _
from frappe import ValidationError
from frappe.utils.file_manager import save_file
from frappe.utils import getdate


def validate_filters(filters):
    # if not filters:
    #     raise frappe.ValidationError(_("Filters are required for this report."))
    # if not isinstance(filters, dict):
    #     raise frappe.ValidationError(_("Invalid filters format. Filters should be a dictionary."))
    if not filters.starting_posting_date or not filters.ending_posting_date:
        frappe.throw(_("From Date and To Date are required."))
    
    if getdate(filters.starting_posting_date) > getdate(filters.ending_posting_date):
        frappe.throw(_("From Date cannot be after To Date."))

def get_columns():
    # Define columns with field names and labels
    return [
        {"label": "Sr", "fieldname": "sr", "fieldtype": "Int", "width": 50, "align": "left", "style": "font-weight: bold;"},
        {"label": "ID", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 120, "align": "left", "style": "font-weight: bold;"},
        {"label": "Docstatus", "fieldname": "docstatus", "fieldtype": "Int", "width": 80, "align": "left", "style": "font-weight: bold;"},
        {"label": "Sales Type", "fieldname": "sales_type", "fieldtype": "Data", "width": 120, "align": "left", "style": "font-weight: bold;"},
        {"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80, "align": "left", "style": "font-weight: bold;"},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Grand Total (Company Currency)", "fieldname": "grand_total", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Total Taxes and Charges (Company Currency)", "fieldname": "total_taxes_and_charges", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Cluster Manager", "fieldname": "cluster_manager", "fieldtype": "Data", "width": 150, "align": "left", "style": "font-weight: bold;"},
        {"label": "Cluster", "fieldname": "cluster", "fieldtype": "Data", "width": 100, "align": "left", "style": "font-weight: bold;"},
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100, "align": "left", "style": "font-weight: bold;"},
        {"label": "Net Total (Company Currency)", "fieldname": "net_total", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Paid Amount (Company Currency)", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Regional Manager", "fieldname": "regional_manager", "fieldtype": "Data", "width": 150, "align": "left", "style": "font-weight: bold;"},
        {"label": "Total (Company Currency)", "fieldname": "total", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Zonal Manager", "fieldname": "zonal_manager", "fieldtype": "Data", "width": 150, "align": "left", "style": "font-weight: bold;"},
        {"label": "Amount (Company Currency)", "fieldname": "amount", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Total Advance Amount (Company Currency)", "fieldname": "total_advance", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Outstanding Amount (Company Currency)", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Alias Name", "fieldname": "alias_name", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Item Quantity", "fieldname": "qty", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Unit Rate (Company Currency)", "fieldname": "unit_rate", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Net Amount (Company Currency)", "fieldname": "net_amount", "fieldtype": "Currency", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Item ID", "fieldname": "item_id", "fieldtype": "Data", "width": 120, "align": "left", "style": "font-weight: bold;"},
    ]

def get_data(filters):
    # print(f"filters :{filters}")
    try:
        data = []
        
        conditions = []
        if filters.custom_zonal_manager:
            conditions.append(f"si.custom_zone = '{filters.custom_zonal_manager}'")
        if filters.custom_regional_manager:
            conditions.append(f"si.custom_regional_manager = '{filters.custom_regional_manager}'")
        if filters.custom_cluster:
            conditions.append(f"si.custom_cluster = '{filters.custom_cluster}'")
        if filters.custom_cluster_manager:
            conditions.append(f"si.custom_cluster = '{filters.custom_cluster_manager}'")
        if filters.customer_name:
            conditions.append(f"si.customer = '{filters.customer_name}'")
        if filters.starting_posting_date and filters.ending_posting_date:
            conditions.append(f"si.posting_date BETWEEN '{filters.starting_posting_date}' AND '{filters.ending_posting_date}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # print(f"get_data:{filters}")
        # print(f"get_data where_clause:{where_clause}")

        # invoices = frappe.db.sql(f"""
        #                 SELECT
        #                     si.name, si.docstatus, si.currency, si.customer_name, si.grand_total, 
        #                     si.total_taxes_and_charges, si.posting_date, si.net_total, 
        #                     si.paid_amount,si.outstanding_amount, si.total FROM
        #                     `tabSales Invoice` si
        #                 WHERE {where_clause}
        #                 ORDER BY si.posting_date DESC
        #             """, as_dict=True)

        invoices = frappe.db.sql(f"""
                        SELECT
                            si.name,
                            si.docstatus,
                            si.currency,
                            si.customer_name,
                            si.grand_total,
                            si.total_taxes_and_charges,
                            si.posting_date,
                            si.net_total,
                            si.paid_amount,
                            si.total_advance,
                            si.custom_zone,
                            si.custom_zonal_manager,
                            si.custom_region,
                            si.custom_regional_manager,
                            si.custom_cluster,
                            si.custom_cluster_manager,
                            c.customer_type,		
                            COALESCE(si.outstanding_amount, 0.0) AS outstanding_amount,
                            si.total 
                        FROM
                            `tabSales Invoice` si 
                            left join `tabCustomer` c on c.name=si.customer_name 
                        WHERE {where_clause} 
                        ORDER BY si.posting_date DESC
                    """, as_dict=True)
        
        print(f"get_data invoices :{invoices}")

        if not invoices:
            frappe.throw(_("No Sales Invoices found for the given filters."))

        for idx, inv in enumerate(invoices, 1):
            items = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": inv.name},
                fields=["amount", "item_name", "qty", "rate", "net_amount", "name as item_id"]
            )
            
            if not items:
                frappe.throw(_("No items found for Sales Invoice {0}").format(inv.name))
            
            count = 0
            for item in items:
                if count == 0:
                    count=1
                    row = {
                        "sr": idx,
                        "name": inv.name,
                        "docstatus": inv.docstatus,
                        "sales_type": inv.customer_type,#get_sales_type(inv.name),
                        "currency": inv.currency,
                        "customer_name": inv.customer_name,
                        "grand_total": "{:.2f}".format(inv.grand_total),
                        "total_taxes_and_charges": "{:.2f}".format(inv.total_taxes_and_charges),
                        "cluster_manager":inv.custom_cluster_manager, #get_cluster_manager(inv.name),
                        "cluster": inv.custom_cluster, #get_cluster(inv.name),
                        "posting_date": inv.posting_date,
                        "net_total": "{:.2f}".format(inv.net_total),
                        "paid_amount": "{:.2f}".format(inv.paid_amount),
                        "regional_manager": inv.custom_regional_manager,#get_regional_manager(inv.name),
                        "total": "{:.2f}".format(inv.total),
                        "zonal_manager": inv.custom_zonal_manager,#get_zonal_manager(inv.name),
                        "amount": "{:.2f}".format(item.amount),
                        "total_advance":"{:.2f}".format(inv.total_advance),
                        "outstanding_amount":"{:.2f}".format(inv.outstanding_amount),
                        "item_name": item.item_name,
                        "alias_name": get_alias_name(item.item_name),
                        "qty": item.qty,
                        "unit_rate": "{:.2f}".format(item.rate),
                        "net_amount": "{:.2f}".format(item.net_amount),
                        "item_id": item.item_id,
                    }
                else:
                    row={
                        "amount": "{:.2f}".format(item.amount),
                        "item_name": item.item_name,
                        "alias_name": get_alias_name(item.item_name),
                        "qty": item.qty,
                        "unit_rate": "{:.2f}".format(item.rate),
                        "net_amount": "{:.2f}".format(item.net_amount),
                        "item_id": item.item_id,
                    }      
                data.append(row)
        
        total_row = calculate_totals(data)
        data.append(total_row)
        
        return data

    except Exception as e:
        print(f"Error retrieving data: {e}")
        frappe.throw(_("Error retrieving data: {0}").format(str(e)))

def calculate_totals(data):
    total_grand_total = sum(float(d.get("grand_total", 0)) for d in data)
    total_paid_amount = sum(float(d.get("paid_amount", 0)) for d in data)
    total_net_total = sum(float(d.get("net_total", 0)) for d in data)
    return {
        "sr": "",
        "name": "Total",
        "grand_total": "{:.2f}".format(total_grand_total),
        "paid_amount": "{:.2f}".format(total_paid_amount),
        "net_total": "{:.2f}".format(total_net_total)
    }

def generate_excel(columns, data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Invoice Report"

    # Write headers
    headers = [col["label"] for col in columns]
    ws.append(headers)

    # Write data rows
    for row in data:
        ws.append([row.get(col["fieldname"]) for col in columns])

    # Save Excel to a byte stream
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return excel_file


def get_sales_type(invoice_name):
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", invoice_name)
        customer = frappe.get_doc("Customer", sales_invoice.customer)
        return customer.customer_type
    except Exception as e:
        frappe.throw(_("Error fetching sales type: {0}").format(str(e)))


def get_cluster_manager(invoice_name):
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", invoice_name)
        return sales_invoice.custom_cluster_manager or "Not Assigned"
    except Exception as e:
        frappe.throw(_("Error fetching cluster manager: {0}").format(str(e)))

def get_cluster(invoice_name):
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", invoice_name)
        return sales_invoice.custom_cluster or "Not Assigned"
    except Exception as e:
        frappe.throw(_("Error fetching cluster: {0}").format(str(e)))

def get_regional_manager(invoice_name):
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", invoice_name)
        return sales_invoice.custom_regional_manager or "Not Assigned"
    except Exception as e:
        frappe.throw(_("Error fetching regional manager: {0}").format(str(e)))

def get_zonal_manager(invoice_name):
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", invoice_name)
        return sales_invoice.custom_zonal_manager or "Not Assigned"
    except Exception as e:
        frappe.throw(_("Error fetching zonal manager: {0}").format(str(e)))


def get_alias_name(item_name):
    try:
        query = """
            SELECT custom_alias_name 
            FROM tabItem
            WHERE item_name = %s
        """
        result = frappe.db.sql(query, item_name, as_dict=True)
        
        if result:
            return result[0].get("custom_alias_name") or item_name
        else:
            return item_name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching alias name: {0}").format(str(e)))
        frappe.throw(_("Error fetching alias name: {0}").format(str(e)))


@frappe.whitelist(allow_guest=True)
def generate_and_download_sales_invoice_report(filters=None):
    try:
        # print(f"generate_and_download_sales_invoice_report filters :{filters}")

        if filters is not None:
            try:
                filters = frappe.parse_json(filters)
                # filters = frappe._dict(filters)
                validate_filters(filters)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), _("Error fetching : {0}").format(str(e)))
                return {'error': str(e)}
    
        
        # Get columns and data
        columns = get_columns()

        # print(f"columns :{columns}")

        data = get_data(filters)
        # print(f"data :{data}")

        
        if not data:
            frappe.log_error(frappe.get_traceback(), _("No data found for the given filters"))
            frappe.throw(_("No data found for the given filters."))


        # Generate Excel file using openpyxl
        excel_file = generate_excel(columns, data)

        # Save file to private folder
        file_name = "Sales_Invoice_Report.xlsx"
        file_data = excel_file.getvalue()
        
        # Create a file record in Frappe
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "file_url": "/private/files/" + file_name,
            "is_private": 1,
            "content": file_data
        })
        file_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        # Return file URL
        # return {"file_url": file_doc.file_url}
        return {
            'file_url': file_doc.file_url,
            'file_name': file_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to generate report"))
        return {"error": _("An error occurred: {0}").format(str(e))}    