import frappe
from io import BytesIO
from openpyxl import Workbook
from frappe import _
from frappe import ValidationError
from frappe.utils.file_manager import save_file
from frappe.utils import getdate
import os
from frappe.core.doctype.communication.email import make


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
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100, "align": "left", "style": "font-weight: bold;"},
        {"label": "ID", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 120, "align": "left", "style": "font-weight: bold;"},
        {"label": "Docstatus", "fieldname": "docstatus", "fieldtype": "Int", "width": 80, "align": "left", "style": "font-weight: bold;"},
        {"label": "Sales Type", "fieldname": "sales_type", "fieldtype": "Data", "width": 120, "align": "left", "style": "font-weight: bold;"},
        {"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80, "align": "left", "style": "font-weight: bold;"},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Customer State", "fieldname": "custom_state", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Customer Category", "fieldname": "customer_category", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Cluster Manager", "fieldname": "cluster_manager", "fieldtype": "Data", "width": 150, "align": "left", "style": "font-weight: bold;"},
        {"label": "Cluster", "fieldname": "cluster", "fieldtype": "Data", "width": 100, "align": "left", "style": "font-weight: bold;"},
        {"label": "Regional Manager", "fieldname": "regional_manager", "fieldtype": "Data", "width": 150, "align": "left", "style": "font-weight: bold;"},
        {"label": "Zonal Manager", "fieldname": "zonal_manager", "fieldtype": "Data", "width": 150, "align": "left", "style": "font-weight: bold;"},
        {"label": "Tax Category (Company Currency)", "fieldname": "tax_category", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Total Taxes and Charges (Company Currency)", "fieldname": "total_taxes_and_charges", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Net Total (Company Currency)", "fieldname": "net_total", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Grand Total (Company Currency)", "fieldname": "grand_total", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Paid Amount (Company Currency)", "fieldname": "paid_amount", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Total (Company Currency)", "fieldname": "total", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Total Advance Amount (Company Currency)", "fieldname": "total_advance", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Outstanding Amount (Company Currency)", "fieldname": "outstanding_amount", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Alias Name", "fieldname": "alias_name", "fieldtype": "Data", "width": 200, "align": "left", "style": "font-weight: bold;"},
        {"label": "Item Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Unit Rate (Company Currency)", "fieldname": "unit_rate", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        {"label": "Net Amount (Company Currency)", "fieldname": "net_amount", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
        # {"label": "Item ID", "fieldname": "item_id", "fieldtype": "Data", "width": 120, "align": "left", "style": "font-weight: bold;"},
        {"label": "Amount (Company Currency)", "fieldname": "amount", "fieldtype": "Float", "width": 180, "align": "right", "style": "font-weight: bold;"},
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
            conditions.append(f"si.custom_cluster_manager = '{filters.custom_cluster_manager}'")
        if filters.customer_name:
            conditions.append(f"si.customer = '{filters.customer_name}'")
        if filters.starting_posting_date and filters.ending_posting_date:
            conditions.append(f"si.posting_date BETWEEN '{filters.starting_posting_date}' AND '{filters.ending_posting_date}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"

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
                            c.customer_group,	
                            c.custom_customer_category,
                            c.custom_state,
                            c.tax_category,
                            c.default_currency,				
                            COALESCE(si.outstanding_amount, 0.0) AS outstanding_amount,
                            si.total 
                        FROM
                            `tabSales Invoice` si 
                            left join `tabCustomer` c on c.name=si.customer_name 
                        WHERE {where_clause} 
                        ORDER BY si.posting_date DESC
                    """, as_dict=True)
        
        # print(f"get_data invoices :{invoices}")

        if not invoices:
            frappe.throw(_("No Sales Invoices found for the given filters."))

        for idx, inv in enumerate(invoices, 1):
            items = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": inv.name},
                fields=["amount", "item_name", "qty", "rate", "net_amount", "name as item_id"]
            )
            
            if not items:
                frappe.log_error(frappe.get_traceback(), _("No items found for Sales Invoice: {0}").format(str(e)))
                frappe.throw(_("No items found for Sales Invoice {0}").format(inv.name))

            for item_idx, item in enumerate(items):
                # Include common details only in the first row for the invoice
                row = {
                    "sr": idx if item_idx == 0 else "",
                    "name": inv.name if item_idx == 0 else "",
                    "docstatus": inv.docstatus if item_idx == 0 else "",
                    "sales_type": inv.customer_type if item_idx == 0 else "",
                    "currency": inv.currency if item_idx == 0 else "",
                    "customer_name": inv.customer_name if item_idx == 0 else "",
                    "custom_state":inv.custom_state if item_idx == 0 else "",
                    "customer_category":inv.custom_customer_category if item_idx == 0 else "",
                    "grand_total":float( "{:.2f}".format(float(inv.grand_total))) if item_idx == 0 else "",
                    "tax_category":inv.tax_category if item_idx == 0 else "",
                    "total_taxes_and_charges": float("{:.2f}".format(float(inv.total_taxes_and_charges))) if item_idx == 0 else "",
                    "cluster_manager": inv.custom_cluster_manager if item_idx == 0 else "",
                    "cluster": inv.custom_cluster if item_idx == 0 else "",
                    "posting_date": inv.posting_date if item_idx == 0 else "",
                    "net_total": float("{:.2f}".format(float(inv.net_total))) if item_idx == 0 else "",
                    "paid_amount": float("{:.2f}".format(float(inv.paid_amount))) if item_idx == 0 else "",
                    "regional_manager": inv.custom_regional_manager if item_idx == 0 else "",
                    "total": float("{:.2f}".format(float(inv.total))) if item_idx == 0 else "",
                    "zonal_manager": inv.custom_zonal_manager if item_idx == 0 else "",
                    "total_advance": float("{:.2f}".format(float(inv.total_advance))) if item_idx == 0 else "",
                    "outstanding_amount": float("{:.2f}".format(float(inv.outstanding_amount))) if item_idx == 0 else "",
                    # Item-specific details
                    "item_name": item.item_name,
                    "alias_name": get_alias_name(item.item_name),
                    "qty": item.qty,
                    "unit_rate": float("{:.2f}".format(float(item.rate))),
                    "net_amount": float("{:.2f}".format(float(item.net_amount))),
                    # "item_id": item.item_id,
                    "amount": float("{:.2f}".format(float(item.amount))),
                }
                data.append(row)
        
        total_row = calculate_totals(data)
        data.append(total_row)
        
        return data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error retrieving data: {0}").format(str(e)))
        frappe.throw(_("Error retrieving data: {0}").format(str(e)))

def calculate_totals(data):
    total_grand_total = sum(float(d.get("grand_total", 0)) for d in data if d.get("grand_total"))
    total_paid_amount = sum(float(d.get("paid_amount", 0)) for d in data if d.get("paid_amount"))
    total_net_total = sum(float(d.get("net_total", 0)) for d in data if d.get("net_total"))
    total_advance_amt = sum(float(d.get("total_advance", 0)) for d in data if d.get("total_advance"))
    total_outstanding_amt = sum(float(d.get("outstanding_amount", 0)) for d in data if d.get("outstanding_amount"))
    total_taxes_and_charges = sum(float(d.get("total_taxes_and_charges", 0)) for d in data if d.get("total_taxes_and_charges"))
    return {
        "sr": "",
        "name": "Total",
        "grand_total": float("{:.2f}".format(total_grand_total)),
        "paid_amount": float("{:.2f}".format(total_paid_amount)),
        "total_advance": float("{:.2f}".format(total_advance_amt)),
        "outstanding_amount": float("{:.2f}".format(total_outstanding_amt)),
        "total_taxes_and_charges":float("{:.2f}".format(total_taxes_and_charges)),
        "net_total": float("{:.2f}".format(total_net_total))
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


        file_path = file_doc.file_url
        recipient_email = "adithyans@windrolinx.com"
        subject = "Sales Invoice  Report"
        message = "Please find the attached report."

        frappe.sendmail(
            recipients=[recipient_email],
            subject=subject,
            message=message,
            # attachments=[file_doc.file_url]
             attachments=[{
                "fname": file_doc.file_name,
                "fcontent": file_data  # Use the file data here
            }]
        )

        # Return file URL
        # return {"file_url": file_doc.file_url}
        return {
            'file_url': file_doc.file_url,
            'file_name': file_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to generate report"))
        return {"error": _("An error occurred: {0}").format(str(e))}    


def convert_html_to_pdf(html_file, output_pdf):
    try:
        # Read the HTML file and convert to PDF
        HTML(html_file).write_pdf(output_pdf)
        print(f"Converted {html_file} to {output_pdf}")
    except Exception as e:
        print(f"Error: {e}")


def attach_pdf_to_email(pdf_path, recipient_email):
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
            file_doc = save_file(
                os.path.basename(pdf_path),
                pdf_content,
                doctype="File",
                is_private=1
            )
            frappe.sendmail(
                recipients=[recipient_email],
                subject="Your PDF Report",
                message="Please find the attached PDF report.",
                attachments=[{
                    "fname": file_doc.file_name,
                    "fcontent": pdf_content
                }]
            )
        frappe.msgprint(f"Email sent to {recipient_email}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in Sending Email")
        frappe.throw(f"An error occurred: {str(e)}")