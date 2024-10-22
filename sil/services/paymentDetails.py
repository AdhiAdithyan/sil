import frappe
from frappe.utils import getdate
from datetime import datetime,date
from frappe.utils import nowdate
from frappe import _
import re
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry



def enterDetailsToSubTable(outstanding_invoice, outstanding_order, advance_details, entry_table):
    def is_duplicate(entry, table):
        """Check if the entry already exists in the table."""
        for existing_entry in table:
            if (existing_entry['customer'] == entry['customer'] and
                existing_entry['id'] == entry['id'] and
                existing_entry['type'] == entry['type']):
                return True
        return False

    if outstanding_invoice:
        print("outstanding_invoice")
        for item in outstanding_invoice:
            name = item.get('name')
            customer = item.get('customer')
            outstanding_amount = item.get('outstanding_amount')
            posting_date = item.get('posting_date')
            due_date = item.get('due_date')
            
            new_entry = {
                "customer": customer,
                "id": name,
                "pending_amount": outstanding_amount,
                "amount": 0,
                "type": "Sales Invoice"
            }
            if not is_duplicate(new_entry, entry_table):
                entry_table.append(new_entry)

    if outstanding_order:
        print("outstanding_order")
        # ['name', 'customer', 'grand_total', 'transaction_date', 'delivery_date'])
        for item in outstanding_order:
            print(f"item: {item}")
            name = item.get('name')
            customer = item.get('customer')
            outstanding_amount = item.get('grand_total')
            posting_date = item.get('transaction_date')
            due_date = item.get('delivery_date')

            new_entry = {
                "customer": customer,
                "id": name,
                "pending_amount": outstanding_amount,
                "amount": 0,
                "type": "Sales Order"
            }
            if not is_duplicate(new_entry, entry_table):
                entry_table.append(new_entry)

    if advance_details:
        print("advance_details")
        customer = advance_details.get('customer')
        typeName = advance_details.get('type')
        
        new_entry = {
            "customer": customer,
            "pending_amount": 0,
            "amount": 0,
            "type": typeName
        }
        if not is_duplicate(new_entry, entry_table):
            entry_table.append(new_entry)
        print(f"advance_details item: {advance_details}")

    print(f"entry_table123: {entry_table}")
    return entry_table



def get_outstanding_invoices(customer_name=None, posting_date_start=None, posting_date_end=None):
    filters = {
        'status': ['in', ['Unpaid', 'Partly Paid']]
    }
    
    if customer_name:
        filters['customer'] = customer_name
    
    if posting_date_start and posting_date_end:
        filters['posting_date'] = ['between', [posting_date_start, posting_date_end]]
    elif posting_date_start:
        filters['posting_date'] = ['>=', posting_date_start]
    elif posting_date_end:
        filters['posting_date'] = ['<=', posting_date_end]
    
    outstanding_invoices = frappe.get_all('Sales Invoice', 
                                          filters=filters,
                                          fields=['name', 'customer', 'outstanding_amount', 'posting_date', 'due_date'])
    
    # Convert datetime.date objects to strings in the format 'YYYY-MM-DD'
    for invoice in outstanding_invoices:
        if isinstance(invoice['posting_date'], date):
            invoice['posting_date'] = invoice['posting_date'].strftime('%Y-%m-%d')
        if isinstance(invoice['due_date'], date):
            invoice['due_date'] = invoice['due_date'].strftime('%Y-%m-%d')
    
    return outstanding_invoices



def get_outstanding_orders(customer_name=None, posting_date_start=None, posting_date_end=None):
    filters = {
        'status': 'To Deliver and Bill'
    }
    
    if customer_name:
        filters['customer'] = customer_name
    
    if posting_date_start and posting_date_end:
        filters['transaction_date'] = ['between', [posting_date_start, posting_date_end]]
    elif posting_date_start:
        filters['transaction_date'] = ['>=', posting_date_start]
    elif posting_date_end:
        filters['transaction_date'] = ['<=', posting_date_end]
    
    outstanding_orders = frappe.get_all('Sales Order', 
                                        filters=filters,
                                        fields=['name', 'customer', 'grand_total', 'transaction_date', 'delivery_date'])
    return outstanding_orders



@frappe.whitelist()
def get_filtered_receipt_info(formData):
    try:
        # # Check the type of formData
        # if not isinstance(formData, dict):
        #     raise ValueError("formData is not a dictionary")
        formData=frappe.parse_json(formData)
        # Extract form data
        start_date = getdate(formData.get('start_date'))
        end_date = getdate(formData.get('end_date'))
        main_table = formData.get('main_document', {})
        customer_table = formData.get('child_tables', {}).get('customer', [])
        entry_table = formData.get('child_tables', {}).get('entries', [])

        print(f"start_date: {start_date}")
        print(f"end_date: {end_date}")
        print(f"main_table: {main_table}")
        print(f"customer_table: {customer_table}")
        print(f"entry_table: {entry_table}")
        outstanding_invoice={}
        outstanding_order={}
        advance_details={}
        for item in customer_table:
            # print(f"Field Details:{item}")
            customerName=None
            typeName=None
            for key, value in item.items():
                    if key == "customer":
                        customerName=value
                    if key == "type":    
                        typeName=value
            
                    if typeName == "Sales Invoice":
                        outstanding_invoice = get_outstanding_invoices(customerName,start_date,end_date)
                    elif typeName == "Sales Order":
                        outstanding_order = get_outstanding_orders(customerName,start_date,end_date) 
                    elif typeName == "Advance": 
                        advance_details = {"customer":customerName,"type":typeName}

                        print(f"{customerName}: {typeName}")
        
        enterDetailsToSubTable(outstanding_invoice,outstanding_order,advance_details,entry_table)
        print(f"outstanding_invoice:{outstanding_invoice}")
        print(f"outstanding_order:{outstanding_order}")
        print(f"advance_details:{advance_details}")
        return {"success": True,"message":formData}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in get_filtered_receipt_info')
        print(f"Error:{str(e)}")
        print(f"Error:{frappe.get_traceback()}")
        return {'error': str(e)}     



@frappe.whitelist()
def process_batch_payment(total_amount, entries):
    payment_type = "Pay"  # Assuming this is a payment to multiple customers
    company = "YourCompanyName"
    paid_from = "BankAccount1"
    paid_from_account_currency = "INR"
    paid_to_account_currency = "INR"

    remaining_amount = float(total_amount)

    for entry in entries:
        party = entry["party"]
        paid_to = entry["paid_to"]
        references = entry["references"]

        # Calculate the total amount to be allocated to this customer
        allocated_amount = sum(float(ref["allocated_amount"]) for ref in references)
        
        if remaining_amount >= allocated_amount:
            paid_amount = allocated_amount
            remaining_amount -= allocated_amount
        else:
            paid_amount = remaining_amount
            remaining_amount = 0

        received_amount = paid_amount

        try:
            payment_entry_name = create_payment_entry(payment_type, "Customer", party, company, 
                                                      paid_amount, received_amount, paid_from, 
                                                      paid_from_account_currency, paid_to, 
                                                      paid_to_account_currency, references)
            frappe.msgprint(f"Payment Entry {payment_entry_name} created and submitted successfully for {party}.")
        except Exception as e:
            frappe.throw(f"Failed to create payment entry for {party}: {e}")

        if remaining_amount <= 0:
            break

    return True


def create_payment_entry(payment_type, party_type, party, company, paid_amount, received_amount, 
                         paid_from, paid_from_account_currency, paid_to, paid_to_account_currency, references):
    # Create a new Payment Entry document
    pe = frappe.new_doc("Payment Entry")
    
    # Set the basic details
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party
    pe.company = company
    pe.paid_amount = paid_amount
    pe.received_amount = received_amount
    pe.paid_from = paid_from
    pe.paid_from_account_currency = paid_from_account_currency
    pe.paid_to = paid_to
    pe.paid_to_account_currency = paid_to_account_currency

    # Add references if any
    for ref in references:
        pe.append("references", {
            "reprocess_batch_paymentference_doctype": ref["reference_doctype"],
            "reference_name": ref["reference_name"],
            "due_date": ref["due_date"],
            "total_amount": ref["total_amount"],
            "outstanding_amount": ref["outstanding_amount"],
            "allocated_amount": ref["allocated_amount"]
        })
    
    # Validate and insert the payment entry
    pe.validate()
    pe.insert()
    
    # Submit the payment entry
    pe.submit()
    
    frappe.db.commit()
    
    return pe.name



def create_advance_payment_journal_entry(customer_name, debit_account, credit_account, amount):
    try:
        # Validate if the customer exists
        if not frappe.db.exists("Customer", customer_name):
            frappe.throw(_("Customer {0} does not exist").format(customer_name))

        # Create a new Journal Entry document using the JournalEntry class
        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.posting_date = nowdate()
        journal_entry.voucher_type = "Journal Entry"
        journal_entry.user_remark = "Advance Payment"
        journal_entry.company = frappe.defaults.get_defaults().get('company')

        # Add the debit and credit accounts
        journal_entry.append("accounts", {
            "account": debit_account,
            "party_type": "Customer",
            "party": customer_name,
            "debit_in_account_currency": amount,
            "credit_in_account_currency": 0
        })
        journal_entry.append("accounts", {
            # "account": credit_account,
            "account": debit_account,
            "party_type": "Customer",
            "party": customer_name,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": amount
        })
        
        # Insert and submit the journal entry
        journal_entry.insert()
        journal_entry.submit()

        # Commit the transaction
        frappe.db.commit()

        frappe.msgprint(_("Advance Payment Journal Entry {0} created and submitted successfully.").format(journal_entry.name))
    
    except Exception as e:
        # Rollback in case of any error
        frappe.db.rollback()
        frappe.throw(_("An error occurred while creating the advance payment journal entry: {0}").format(str(e)))


def create_payment_entry_new(payment_type, party_type, party, company,
 paid_amount, received_amount,paid_from, paid_from_account_currency,
  paid_to, paid_to_account_currency, references):
    # Create a new Payment Entry document
    pe = frappe.new_doc("Payment Entry")
    
    # Set the basic details
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party
    pe.company = company
    pe.paid_amount = paid_amount
    pe.received_amount = received_amount
    pe.paid_from = paid_from
    pe.paid_from_account_currency = paid_from_account_currency
    pe.paid_to = paid_to
    pe.paid_to_account_currency = paid_to_account_currency

    pe.append("references", {
            "reference_doctype": ref["reference_doctype"],
            "reference_name": ref["reference_name"],
            "due_date": ref["due_date"],
            "total_amount": ref["total_amount"],
            "outstanding_amount": ref["outstanding_amount"],
            "allocated_amount": ref["allocated_amount"]
        })
    
    # Validate and insert the payment entry
    pe.validate()
    pe.insert()
    
    # Submit the payment entry
    pe.submit()
    
    frappe.db.commit()
    
    return pe.name


@frappe.whitelist()
def paymentEntry(frm,formData):
    # frm is passed as a JSON string, so we need to parse it
    frm_doc = frappe.parse_json(frm)
    formData=frappe.parse_json(formData)
    # Extract form data
    main_table = formData.get('main_document', {})
    customer_table = formData.get('child_tables', {}).get('customer', [])
    entry_table = formData.get('child_tables', {}).get('entries', [])
    
    print(f"main_table: {main_table}")
    print(f"customer_table: {customer_table}")
    print(f"entry_table: {entry_table}")
    
    print("Entries")
    total_amount_payed = 0
    company_name=None
    credit_account=None
    debit_account=None
    currency=None

    for entry in main_table:
        total_amount_payed = main_table['amount']
        company_name = main_table['company']
    
        print(f"{entry}:{main_table[entry]}")

    company_details = frappe.db.sql("""Select * from `tabCompany` where `name`=%s;
    """,(company_name,),as_dict=True)
    
    print("Company details")
    print(f"Company details:{str(company_details)}")
    """
    company_name
    abbr
    default_currency
    default_cash_account
    default_receivable_account
    default_payable_account
    pan
    gstin
    default_gst_rate
    cost_center
    depreciation_cost_center
    """
    for company in company_details:
        for key, value in company.items():
            print(f"{key}: {value}")
            if key == 'default_payable_account':
                credit_account=value
            if key == 'default_receivable_account':   
                debit_account=value
            if key == 'default_currency':   
                currency=value    

    payment_type = "Receive"  # Assuming this is a payment to multiple customers
    company = company_name
    paid_from = debit_account
    paid_from_account_currency = currency
    paid_to_account_currency = currency

    for entry in entry_table:
        # print(f"Name: {entry['name']}")
        # print(f"Owner: {entry['owner']}")
        # print(f"Creation: {entry['creation']}")
        # print(f"Modified: {entry['modified']}")
        # print(f"Modified By: {entry['modified_by']}")
        # print(f"Docstatus: {entry['docstatus']}")
        # print(f"Index: {entry['idx']}")
        # print(f"Customer: {entry['customer']}")
        # print(f"ID: {entry['id']}")
        # print(f"Pending Amount: {entry['pending_amount']}")
        # print(f"Amount: {entry['amount']}")
        # print(f"Type: {entry['type']}")
        # print(f"Parent: {entry['parent']}")
        # print(f"Parentfield: {entry['parentfield']}")
        # print(f"Parenttype: {entry['parenttype']}")
        # print(f"Doctype: {entry['doctype']}")
        # print("\n")
        if entry['type']=="Sales Invoice":
            print("Navigate to Sales Invoice section in payment entry")
        elif entry['type']=="Sales Order":
            print("Navigate to Sales Order section in payment entry") 
        elif entry['type']=="Advance":
            print("Navigate to Advance section in journal") 
            # create_advance_payment_journal_entry(entry['customer'],
            # debit_account,credit_account,entry['amount'])       

    return {"message":"Save button clicked","result":f"{str(frm_doc)}"}