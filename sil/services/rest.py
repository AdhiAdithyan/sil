# This file is calling all the available services in a common file for easy access.
# from erpnext.accounts.doctype.sales_invoice.api import getAllCustDetails
import frappe
from frappe import _
import sil.services.customer_api as cust_api
import sil.services.address_api as address_api
import sil.services.cluster_api as cluster_api
import sil.services.sales_invoice_api as invoice_api
import sil.services.employee_checkin_api as emp_api
import sil.services.stock_item_api as stock_api
import sil.services.sales_order_api as order_api
import sil.services.employee_check_in_report_api as emp_report_api


#for getting all the address details
@frappe.whitelist(allow_guest=True)
def getAllAddressDetails():
    return address_api.getAllAddressDetails()


#for getting all the available cluster details
@frappe.whitelist(allow_guest=True)
def getAllClusterDetails():
    return cluster_api.getAllClusterDetails()


#for getting all the available cluster details where the upload statusw is zero
@frappe.whitelist(allow_guest=True)
def getAllClustWithStatus(data):
    #{"Status":""}
    return cluster_api.getAllClustWithStatus(data)


#for getting all the available cluster details with the given cluster name
@frappe.whitelist(allow_guest=True)
def updateClusterStatus(data):    
    #{"cluster_name":""}
    return cluster_api.updateClusterStatus(data)


#for getting all the available customer details
@frappe.whitelist(allow_guest=True)
def getAllCustDetails():
    return cust_api.getAllCustomerDetails()


#for getting all the available customer details with upload status 0
@frappe.whitelist(allow_guest=True)
def getAllCustWithStatus(data):
    #{"Status":""}
    return cust_api.getAllCustWithStatus(data)


#for updating the customer details with upload status 0,
#if the given customer name is present in the database
@frappe.whitelist(allow_guest=True)
def updateCustomerUploadStatus(data):   
    #{"cust_name":""} 
    return cust_api.updateCustomerUploadStatus(data)


#for adding new employee check-in details
@frappe.whitelist(allow_guest=True)
def AddCheckInStatus(data):  
    #{"enrollid":126,"name":"Harsh","time":"2024-05-20 13:25:46","mode":8,"inout":0,"event":0}  
    return emp_api.AddCheckInStatus(data)


#for getting all the e-invoice details
@frappe.whitelist(allow_guest=True)
def getAllE_BillDetails():
    return invoice_api.getAllE_BillDetails()


#for getting all the e-invoice details
@frappe.whitelist(allow_guest=True)
def getAllBillDetails():
    return invoice_api.getAllBillDetails()    


#for getting all the e-invoice details with invoice number
@frappe.whitelist(allow_guest=True)
def getAllE_BillDetailsByBillNumber(data):
    #{"InvoiceNo":""}
    return invoice_api.getAllE_BillDetailsByBillNumber(data)


#for getting all the invoice details
@frappe.whitelist(allow_guest=True)
def getAllInvoiceDetails():
    return invoice_api.getAllInvoiceDetails()


#for getting all the invoice details with the given status
@frappe.whitelist(allow_guest=True)
def getAllInvoiceDetailsWithStatus(data):   
    #{"InvoiceStatus":""} 
    return invoice_api.getAllInvoiceDetailsWithStatus(data)


#for getting all the invoice item details with the given invoice number
@frappe.whitelist(allow_guest=True)
def getAllInvoiceItemDetails(data): 
    #{"Invoice_no":""}     
    return invoice_api.getAllInvoiceItemDetails(data)


#for updating the upliad status in invoice details with the given invoice number
@frappe.whitelist(allow_guest=True)
def updateInvoiceUploadStatus(data):  
    #{"Invoice_no":""}  
    return invoice_api.updateInvoiceUploadStatus(data)


#for updating the upliad status in invoice details with the given date
@frappe.whitelist(allow_guest=True)
def updateInvoiceStatusWithDate(data):
    #{"posting_date":""}
    return invoice_api.updateInvoiceUploadStatusWithDate(data)

#for getting all the stock details with the given status
@frappe.whitelist(allow_guest=True)
def getAllStockWithUploadStatus(data):
    return stock_api.getAllStockWithUploadStatus(data)


#for getting all stock details
@frappe.whitelist(allow_guest=True)
def getAllStock(): 
    return stock_api.getAllStock()   


@frappe.whitelist(allow_guest=True)
def updateStockItemUploadStatus(data):    
    return stock_api.updateStockItemUploadStatus(data) 


@frappe.whitelist()
def generateSeriesNo(items_series, form_doc):    
    return order_api.generateSeriesNo(items_series, form_doc)


@frappe.whitelist(allow_guest=True)
def sentMailToEmp():
    return emp_report_api.send_combined_daily_checkin_report_to_emp()



@frappe.whitelist(allow_guest=True)
def sentDailyMailToHR():
    return emp_report_api.send_combined_daily_checkin_report_to_hr()



@frappe.whitelist(allow_guest=True)
def sentWeeklyMailToHR():
    return emp_report_api.send_combined_weekly_checkin_report_to_hr()





    





























