import frappe
from frappe import _
import sil.services.customer_api as cust_api
import sil.services.stock_item_api as stock_api
import sil.services.address_api as address_api
import sil.services.sales_invoice_api as invoice_api
import sil.services.tally_api as journal_api



# For getting all customer details
@frappe.whitelist(allow_guest=True)
def getAllCustomerDetails():
    return cust_api.getAllCustomerDetails()


# For getting all customer details with a specific status
@frappe.whitelist(allow_guest=True)
def getAllCustWithStatus(data):
    # Input example: {"Status": ""}
    return cust_api.getAllCustWithStatus(data)


# For updating the upload status of a customer
@frappe.whitelist(allow_guest=True)
def updateCustomerUploadStatus(data):
    # Input example: {"cust_name": ""}
    return cust_api.updateCustomerUploadStatus(data)


# For getting all stock items with upload status
@frappe.whitelist(allow_guest=True)
def getAllStockWithUploadStatus(data):
    # Input example: {"Status": ""}
    return stock_api.getAllStockWithUploadStatus(data)


# For updating the upload status of a stock item
@frappe.whitelist(allow_guest=True)
def updateStockItemUploadStatus(data):
    # Input example: {"stock_item_name": ""}
    return stock_api.updateStockItemUploadStatus(data)


# For getting all address details
@frappe.whitelist(allow_guest=True)
def getAllAddressDetails():
    return address_api.getAllAddressDetails()


# For getting all e-bill details
@frappe.whitelist(allow_guest=True)
def getAllE_BillDetails():
    return invoice_api.getAllE_BillDetails()


# For getting e-bill details by bill number
@frappe.whitelist(allow_guest=True)
def getAllE_BillDetailsByBillNumber(data):
    # Input example: {"InvoiceNo": ""}
    return invoice_api.getAllE_BillDetailsByBillNumber(data)


# For getting all invoice details
@frappe.whitelist(allow_guest=True)
def getAllInvoiceDetails(data):
    # Input example: {"Status": ""}
    return invoice_api.getAllInvoiceDetails(data)


# For getting all invoice details with a specific status
@frappe.whitelist(allow_guest=True)
def getAllInvoiceDetailsWithStatus(data):
    # Input example: {"InvoiceStatus": ""}
    return invoice_api.getAllInvoiceDetailsWithStatus(data)


# For getting all invoice item details with a specific invoice number
@frappe.whitelist(allow_guest=True)
def getAllInvoiceItemDetails(data):
    # Input example: {"Invoice_no": ""}
    return invoice_api.getAllInvoiceItemDetails(data)


# For updating the upload status of an invoice
@frappe.whitelist(allow_guest=True)
def updateInvoiceUploadStatus(data):
    # Input example: {"Invoice_no": ""}
    return invoice_api.updateInvoiceUploadStatus(data)


# For updating the upload status of an invoice by date
@frappe.whitelist(allow_guest=True)
def updateInvoiceUploadStatusWithDate(data):
    # Input example: {"posting_date": ""}
    return invoice_api.updateInvoiceUploadStatusWithDate(data)

# Bank to Suspense and Bank to Party
@frappe.whitelist(allow_guest=True)
def get_payment_entries():
    return journal_api.get_payment_entries()

#Suspense to party and party to suspense
@frappe.whitelist(allow_guest=True)
def get_journal_entries():
    return journal_api.get_journal_entries()

# is tally updated to 1
@frappe.whitelist(allow_guest=True)
def update_payment_entry_tally_status(name):
    return journal_api.update_payment_entry_tally_status(name)

# is tally updated to 1
@frappe.whitelist(allow_guest=True)
def update_journal_entry_tally_status(name):
    return journal_api.update_journal_entry_tally_status(name)