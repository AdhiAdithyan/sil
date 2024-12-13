import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def getLoggedemployee():
    """
    Fetch the company of the logged-in employee using their email.
    """
    # Get the logged-in user's email
    email = frappe.session.user
    if frappe.local.conf.developer_mode:  # For testing purposes
        email = "adithyans@windrolinx.com"

    # Debugging logs
    print(f"Email: {email}")
    print(f"Roles: {frappe.get_roles(email)}")

    # Fetch the employee details linked to the email
    employee_details = frappe.db.sql("""
        SELECT company
        FROM `tabEmployee`
        WHERE %s IN (personal_email, company_email, prefered_email, name)
    """, (email,), as_dict=True)

    return employee_details


@frappe.whitelist(allow_guest=True)
def getAllAccount():
    
    # Fetch the employee details linked to the email
    employee_details = frappe.db.sql("""
        SELECT *
        FROM `tabAccount` where is_group = 0
    """, as_dict=True)

    return employee_details   

@frappe.whitelist(allow_guest=True)
def getAllModeOfPayment():
    
    # Fetch the employee details linked to the email
    employee_details = frappe.db.sql("""
        SELECT *
        FROM `tabMode of Payment`
    """, as_dict=True)

    return employee_details      

@frappe.whitelist(allow_guest=True)
def getAllModeOfPaymentAccount():
    
    # Fetch the employee details linked to the email
    employee_details = frappe.db.sql("""
        SELECT *
        FROM `tabMode of Payment Account`
    """, as_dict=True)

    return employee_details       


@frappe.whitelist(allow_guest=True)
def getAccountByPaymentType(payment_type=None):
    """
    Fetch payment accounts based on the given payment type and logged-in employee's company.
    """
    try:
        # Fetch logged employee details
        logged_emp = getLoggedemployee()
        if not logged_emp:
            return {
                "error": "No employee found for the logged user.",
                "message": "Employee details could not be fetched."
            }

        # Handle multiple companies (if necessary)
        company = logged_emp[0]["company"]  # Assuming the first company is used
        # print(f"Selected Company: {company}")
        # print(f"Selected Company: {payment_type}")

        payment_accounts = frappe.db.sql("""
            SELECT DISTINCT ta.* FROM  `tabAccount` ta
            INNER JOIN `tabMode of Payment` tmop
            ON ta.account_type = tmop.type
            WHERE ta.company = %s AND tmop.mode_of_payment=%s AND a.is_group = 0 
        """, (logged_emp[0]["company"], payment_type,), as_dict=True)

        print(f"Selected payment_accounts: {payment_accounts}")
        # Return fetched data
        return  payment_accounts

    except Exception as e:
        # Log error for debugging
        frappe.log_error(message=frappe.get_traceback(), title="Error fetching account and payment type data")
        return {
            "error": str(e),
            "message": "Failed to fetch account and payment type data. Please check logs for details."
        }



@frappe.whitelist(allow_guest=True)
def getAccount():
    try:
        # SQL query to fetch payment accounts with account type mapping
        payment_account_query = """
            SELECT Distinct
                pma.company,
                pma.default_account,	
                a.account_type,
                pm.type AS payment_mode_type
            FROM `tabMode of Payment Account` pma
            LEFT JOIN `tabMode of Payment` pm ON pm.name = pma.parent
            LEFT JOIN `tabAccount` a ON a.account_type = pm.type 
            where a.is_group=0
        """
        payment_accounts = frappe.db.sql(payment_account_query, as_dict=True)

        # Return the fetched data
        return payment_accounts

    except Exception as e:
        # Log error and return response
        frappe.log_error(message=frappe.get_traceback(), title="Error fetching account and payment type data")
        return {
            "error": str(e),
            "message": "Failed to fetch account and payment type data. Please check logs for details."
        }

    