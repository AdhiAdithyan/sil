import frappe

def get_employee_hierarchy():
    employees = frappe.get_all('Employee', fields=['name', 'reports_to', 'user_id'])
    hierarchy = {}
    
    for emp in employees:
        hierarchy[emp.name] = {
            'reports_to': emp.reports_to,
            'user_id': emp.user_id,
            'subordinates': []
        }

    for emp_name, emp_data in hierarchy.items():
        if emp_data['reports_to'] and emp_data['reports_to'] in hierarchy:
            hierarchy[emp_data['reports_to']]['subordinates'].append(emp_name)

    top_level_managers = [emp_name for emp_name, emp_data in hierarchy.items() if not emp_data['reports_to']]
    
    return hierarchy, top_level_managers

def get_order_details():
    orders = frappe.get_all(
        'Sales Order',
        filters={'status': 'To Deliver and Bill'},
        fields=['name', 'customer', 'total', 'owner']
    )

    item_details = frappe.get_all(
        'Sales Order Item',
        filters={'parent': ['in', [order['name'] for order in orders]]},
        fields=['parent', 'item_name', 'qty', 'rate', 'amount']
    )

    employee_orders = {}
    item_summary = {}

    for order in orders:
        employee_id = frappe.db.get_value('User', {'email': order['owner']}, 'name')
        if employee_id not in employee_orders:
            employee_orders[employee_id] = {
                'orders': [],
                'total_amount': 0,
                'order_count': 0,
                'items': {}
            }
        employee_orders[employee_id]['orders'].append(order)
        employee_orders[employee_id]['total_amount'] += order['total']
        employee_orders[employee_id]['order_count'] += 1

    for item in item_details:
        for employee_id, employee_data in employee_orders.items():
            for order in employee_data['orders']:
                if order['name'] == item['parent']:
                    if item['item_name'] not in employee_data['items']:
                        employee_data['items'][item['item_name']] = {
                            'qty': 0,
                            'amount': 0
                        }
                    employee_data['items'][item['item_name']]['qty'] += item['qty']
                    employee_data['items'][item['item_name']]['amount'] += item['amount']

                    if item['item_name'] not in item_summary:
                        item_summary[item['item_name']] = {
                            'qty': 0,
                            'amount': 0
                        }
                    item_summary[item['item_name']]['qty'] += item['qty']
                    item_summary[item['item_name']]['amount'] += item['amount']

    return employee_orders, item_summary

def send_emails(hierarchy, employee_orders, item_summary, manager):
    manager_data = hierarchy[manager]
    email_recipients = [manager_data['user_id']]
    
    email_content = """
    <style>
    body {
        font-family: Arial, sans-serif;
        color: #333;
        margin: 20px;
    }
    h3, h4 {
        color: #4CAF50;
        margin-top: 30px;
    }
    p {
        font-size: 14px;
        margin: 10px 0;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        border-radius: 5px;
        overflow: hidden;
        background-color: #66FF66;
    }
    th, td {
        border: 2px solid #ddd;
        padding: 15px; /* Increased padding for better spacing */
    }
    th {
        background-color: #006600;
        color: #ffffff;
        text-transform: uppercase;
        font-size: 12px;
    }
    td {
        font-size: 12px;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    tr:hover {
        background-color: #f1f1f1;
    }
    .left-align {
        text-align: left;
    }
    .center-align {
        text-align: center;
    }
    .right-align {
        text-align: right;
    }
    .no-wrap {
        white-space: nowrap;
    }
    </style>
    """

    # email_content = """
    # <style>
    #     body {
    #         font-family: Arial, sans-serif;
    #         color: #333;
    #         margin: 20px;
    #     }
    #     h3, h4 {
    #         color: #4CAF50;
    #         margin-top: 30px;
    #     }
    #     p {
    #         font-size: 14px;
    #         margin: 10px 0;
    #     }
    #     table {
    #         width: 100%;
    #         border-collapse: collapse;
    #         margin-bottom: 20px;
    #         box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    #         border-radius: 5px;
    #         overflow: hidden;
    #         background-color: #66FF66;
    #     }
    #     th, td {
    #         border: 2px solid #ddd;
    #         padding: 10px;
    #     }
    #     th {
    #         background-color: #006600;
    #         color: #ffffff;
    #         text-transform: uppercase;
    #         font-size: 12px;
    #     }
    #     td {
    #         font-size: 12px;
    #     }
    #     tr:nth-child(even) {
    #         background-color: #f9f9f9;
    #     }
    #     tr:hover {
    #         background-color: #f1f1f1;
    #     }
    #     .left-align {
    #         text-align: left;
    #     }
    #     .center-align {
    #         text-align: center;
    #     }
    #     .right-align {
    #         text-align: right;
    #     }
    #     .no-wrap {
    #         white-space: nowrap;
    #     }
    # </style>
    # """
    
    email_content += f"<h3>Order Summary for Team Managed by {manager}</h3>"
    
    total_orders = 0
    total_amount = 0

    email_content += """
    <table>
        <thead>
            <tr>
                <th class="left-align no-wrap">Executive Name</th>
                <th class="center-align no-wrap">Today's Item Quantity</th>
                <th class="right-align no-wrap">Today's Total Item Amount</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for subordinate in manager_data['subordinates']:
        if subordinate in employee_orders:
            order_details = employee_orders[subordinate]
            email_content += f"""
            <tr>
                <td class="left-align no-wrap">{subordinate}</td>
                <td class="center-align no-wrap">{order_details['order_count']}</td>
                <td class="right-align no-wrap">{order_details['total_amount']}</td>
            </tr>
            """
            total_orders += order_details['order_count']
            total_amount += order_details['total_amount']

    email_content += f"""
        <tr>
            <td class="left-align no-wrap">Grand Total</td>
            <td class="center-align no-wrap">{total_orders}</td>
            <td class="right-align no-wrap">{total_amount}</td>
        </tr>
    </tbody>
    </table>
    """

    email_content += "<h3>Item Details</h3>"
    email_content += """
    <table>
        <thead>
            <tr>
                <th class="left-align no-wrap">Item Name</th>
                <th class="center-align no-wrap">Total Quantity</th>
                <th class="right-align no-wrap">Total Amount</th>
            </tr>
        </thead>
        <tbody>
    """
    total_item_count = 0
    total_item_amount = 0

    for item_name, item_data in item_summary.items():
        email_content += f"""
        <tr>
            <td class="left-align no-wrap">{item_name}</td>
            <td class="center-align no-wrap">{item_data['qty']}</td>
            <td class="right-align no-wrap">{item_data['amount']}</td>
        </tr>
        """
        total_item_count += item_data['qty']
        total_item_amount += item_data['amount']
    

    email_content += f"""
        <tr>
            <td class="left-align no-wrap">Grand Total</td>
            <td class="center-align no-wrap">{total_item_count}</td>
            <td class="right-align no-wrap">{total_item_amount}</td>
        </tr>
    </tbody>
    </table>
    """

    email_content += "<h3>Order Details</h3>"
    email_content += """
    <table>
        <thead>
            <tr>
                <th class="left-align no-wrap">Order Number</th>
                <th class="left-align no-wrap">Customer Name</th>
                <th class="left-align no-wrap">Item Name</th>
                <th class="center-align no-wrap">Item Quantity</th>
                <th class="right-align no-wrap">Item Rate</th>
                <th class="right-align no-wrap">Item Amount</th>
                <th class="right-align no-wrap">Tax Rate</th>
                <th class="right-align no-wrap">Tax Amount</th>
                <th class="right-align no-wrap">Today's Total Item Amount</th>
                <th class="left-align no-wrap">Regional Head</th>
                <th class="left-align no-wrap">Team Head</th>
                <th class="left-align no-wrap">Executive I</th>
                <th class="left-align no-wrap">Executive II</th>
                <th class="left-align no-wrap">Current Status</th>
                <th class="left-align no-wrap">Final Status</th>
            </tr>
        </thead>
        <tbody>
    """

    for subordinate in manager_data['subordinates']:
        if subordinate in employee_orders:
            order_details = employee_orders[subordinate]
            for order in order_details['orders']:
                for item_name, item in order_details['items'].items():
                    email_content += f"""
                    <tr>
                        <td class="left-align no-wrap">{order['name']}</td>
                        <td class="left-align">{order['customer']}</td>
                        <td class="left-align">{item_name}</td>
                        <td class="center-align no-wrap">{item['qty']}</td>
                        <td class="right-align no-wrap">{item['rate']}</td>
                        <td class="right-align no-wrap">{item['amount']}</td>
                        <td class="right-align no-wrap">{order.get('tax_rate', 'N/A')}</td>
                        <td class="right-align no-wrap">{order.get('tax_amount', 'N/A')}</td>
                        <td class="right-align no-wrap">{order['total']}</td>
                        <td class="left-align">Regional Head</td>
                        <td class="left-align">Team Head</td>
                        <td class="left-align">Executive I</td>
                        <td class="left-align">Executive II</td>
                        <td class="left-align no-wrap">Current Status</td>
                        <td class="left-align no-wrap">Final Status</td>
                    </tr>
                    """
    
    email_content += """
        </tbody>
    </table>
    """

    frappe.sendmail(
        recipients=email_recipients,
        subject="Order Details",
        message=email_content,
        reference_doctype='Sales Order',
        reference_name=employee_orders[manager]['orders'][0]['name'] if employee_orders[manager]['orders'] else ''
    )

def send_grouped_emails():
    hierarchy, top_level_managers = get_employee_hierarchy()
    employee_orders, item_summary = get_order_details()
    
    for manager in top_level_managers:
        send_emails(hierarchy, employee_orders, item_summary, manager)

send_grouped_emails()
