import frappe

@frappe.whitelist(allow_guest=True)
def get_user_details():
    user_email = frappe.session.user  # Get the logged-in user's email

    user_details = frappe.get_doc("User", user_email)  # Fetch user document
    user_roles = frappe.get_roles(user_email)  # Get user roles
    emp_detail = get_employee_by_email(user_email)  # Get employee details by email
    # emp_list = get_employee()
 
    print(f"user_email:{user_email}")
    print(f"user_details:{user_details}")
    print(f"user_roles:{user_roles}")
    # print(f"emp_list:{emp_list}")
    print(f"emp_detail:{emp_detail}")
    
    # return {
    #     "email": user_email
    # }
    if emp_detail:
        return {
        # "email": user_email,
        # "full_name": user_details.full_name,
        # "user_details": user_details,
        # "emp_detail": emp_detail,
        # "roles": user_roles,
        "cluster_name":emp_detail[0]['cluster'],
        "region_name":emp_detail[0]['region_name'],
        "zone":emp_detail[0]['zone'],
        "emp_name":emp_detail[0]['emp_name']
        
          }
    else:
        return { "error":"No employee details found for the given user."}      

def get_employee_by_email(email):
    # Fetch employees where the given email matches personal_email, company_email, or prefered_email using a raw SQL query
    # employee_details = frappe.db.sql("""
    #     SELECT cm.cluster,cl.cluster_name,
    #     r.region_name,r.parent_zone as zone			
    #     FROM `tabEmployee` e 
    #     LEFT OUTER JOIN `tabCluster Manager` cm ON cm.cluster = e.name 
    #     LEFT OUTER JOIN `tabCluster` cl ON cl.name = cm.cluster
    #     LEFT OUTER JOIN `tabRegion` r ON r.name = cl.cluster_name
    #     WHERE e.personal_email = %s OR e.company_email = %s OR e.prefered_email = %s
    # """, (email, email, email), as_dict=True)
    employee_details = frappe.db.sql("""
        SELECT cm.cluster,cl.cluster_name,
        cm.custom_parent_region as region_name,r.parent_zone as zone,e.name as emp_name			
        FROM `tabEmployee` e 
        LEFT OUTER JOIN `tabCluster Manager` cm ON cm.cluster_manager = e.name 
        LEFT OUTER JOIN `tabCluster` cl ON cl.name = cm.cluster
        LEFT OUTER JOIN `tabRegion` r ON r.name = cm.custom_parent_region	
        WHERE e.personal_email = %s OR e.company_email = %s OR e.prefered_email = %s
    """, (email, email, email), as_dict=True)

    return employee_details


@frappe.whitelist(allow_guest=True)
def getAllEmployee():
    # Fetch employees where the given email matches personal_email, company_email, or prefered_email using a raw SQL query
    employee_details = frappe.db.sql("""
        SELECT *			
        FROM `tabEmployee` """, as_dict=True)

    return employee_details    


@frappe.whitelist(allow_guest=True)
def getAllClusterManager():
    # Fetch employees where the given email matches personal_email, company_email, or prefered_email using a raw SQL query
    employee_details = frappe.db.sql("""
        SELECT *			
        FROM `tabCluster Manager` """, as_dict=True)

    return employee_details    
    

@frappe.whitelist(allow_guest=True)
def getAllCluster():
    # Fetch employees where the given email matches personal_email, company_email, or prefered_email using a raw SQL query
    employee_details = frappe.db.sql("""
        SELECT *			
        FROM `tabCluster` """, as_dict=True)

    return employee_details   
        

@frappe.whitelist(allow_guest=True)
def getAllRegion():
    # Fetch employees where the given email matches personal_email, company_email, or prefered_email using a raw SQL query
    employee_details = frappe.db.sql("""
        SELECT *			
        FROM `tabRegion` """, as_dict=True)

    return employee_details       


@frappe.whitelist(allow_guest=True)
def getAllZone():
    # Fetch employees where the given email matches personal_email, company_email, or prefered_email using a raw SQL query
    employee_details = frappe.db.sql("""
        SELECT *			
        FROM `tabZone` """, as_dict=True)

    return employee_details            

    



