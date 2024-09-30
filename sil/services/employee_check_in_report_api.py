import frappe
from frappe.utils import add_days, nowdate, getdate, format_datetime, time_diff_in_hours
import os
import tempfile
from datetime import timedelta

def convert_hours_to_hms(decimal_hours):
    """Convert decimal hours to hour:min:sec format."""
    total_seconds = int(decimal_hours * 3600)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def fetch_checkins(employee, start_date, end_date):
    """Fetch checkins for an employee between start and end dates."""
    return frappe.get_all('Employee Checkin',
                          filters={'employee': employee, 'time': ['between', [start_date, end_date]]},
                          fields=['employee', 'time', 'log_type'],
                          order_by='time asc')

def generate_report_html(checkins, employee=None):
    """Generate HTML content for checkin report."""
    grouped_checkins = {}
    max_logs_per_day = 0
    
    for checkin in checkins:
        print('Check-in time123')
        print(checkin['time'])
        print(checkin['employee'])
        # checkin_date = format_datetime(checkin['time'], 'YYYY-MM-DD')
        checkin_date = format_datetime(checkin['time'], 'yyyy-MM-dd')

        print(f"checkin_date:{checkin_date}")
        if checkin_date not in grouped_checkins:
            grouped_checkins[checkin_date] = []
        grouped_checkins[checkin_date].append({
            "Emp_Name":checkin['employee'],
            "Time": format_datetime(checkin['time'], 'HH:mm:ss'),
            "Log Type": checkin['log_type']
        })
        max_logs_per_day = max(max_logs_per_day, len(grouped_checkins[checkin_date]))

    html_content = """
    <html>
    <head>
         <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
                color: #333;
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 20px;
            }
            th, td { 
                padding: 10px; 
                text-align: left; 
                border: 1px solid #ddd; 
            }
            th { 
                background-color: #004d80; 
                color: #ffffff;
                font-weight: bold; 
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #e6f7ff;
            }
            h2 {
                text-align: center;
                color: #004d80;
            }
        </style>
    </head>
    <body>
    <table>
        <tr>
            <th>Date</th>
            <th>Employee</th>
            <th>First Check-in Time</th>
            <th>Last Check-out Time</th>
            <th>Total Working Hours</th>"""

    for i in range(1, max_logs_per_day + 1):
        html_content += f"<th>Check-in Detail {i}</th>"
    html_content += "</tr>"

    total_hours = 0
    
    for checkin_date, logs in grouped_checkins.items():
        first_checkin = logs[0]['Time'] if logs else ""
        last_checkout = logs[-1]['Time'] if logs else ""
        daily_hours = time_diff_in_hours(logs[-1]['Time'], logs[0]['Time']) if len(logs) >= 2 else 0
        total_hours += daily_hours

        html_content += f"""
        <tr>
            <td>{checkin_date}</td>
            <td>{employee if employee else logs[0]['Emp_Name']}</td>
            <td>{first_checkin}</td>
            <td>{last_checkout}</td>
            <td>{convert_hours_to_hms(daily_hours)}</td>"""
        
        for log in logs:
            html_content += f"<td>{log['Time']} ({log['Log Type']})</td>"
        
        for _ in range(len(logs), max_logs_per_day):
            html_content += "<td></td>"
        
        html_content += "</tr>"


    html_content += f"""
    <tr style="font-weight: bold; background-color: #004d80; color: #ffffff;">
        <td colspan="4">Total Working Hours</td>
        <td colspan="{max_logs_per_day + 1}">{convert_hours_to_hms(total_hours)}</td>
    </tr>
    </table>
    </body>
    </html>"""
    
    return html_content

def save_html_to_tempfile(html_content, filename):
    """Save HTML content to a temporary file and return the file path."""
    temp_dir = tempfile.mkdtemp()
    filepath = os.path.join(temp_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(html_content.encode('utf-8'))
    return filepath

def send_email_with_attachment(email, subject, message, filepath, filename):
    """Send an email with an attachment."""
    try:
        frappe.sendmail(
            recipients=email,
            subject=subject,
            message=message,
            attachments=[{'fname': filename, 'fcontent': open(filepath, 'rb').read()}]
        )
    finally:
        os.remove(filepath)  # Ensure file is removed after sending email

# def send_employee_checkin_report():
#     employees = frappe.get_all('Employee', filters={'employee_status': 'Active', 'attendance_type': 'Head Office'},
#                                fields=['name', 'personal_email', 'company_email', 'prefered_contact_email'])
    
#     today = getdate(nowdate())
#     start_date = f"{add_days(today, -2)} 00:00:00"
#     end_date = f"{today} 23:59:59"

#     for employee in employees:
#         checkins = fetch_checkins(employee.name, start_date, end_date)
#         if not checkins:
#             continue
        
#         html_content = generate_report_html(checkins, employee.name)
#         filename = f"{employee.name}_Checkin_Report.xls"
#         filepath = save_html_to_tempfile(html_content, filename)

#         email = frappe.db.get_value('User', employee.company_email if employee.prefered_contact_email == 'Company Email' else employee.personal_email, 'email')
#         if email:
#             frappe.sendmail(
#             recipients=email,
#             subject="Daily Check-in Report",
#             message=html_content
#              )


def send_employee_checkin_report():
    # Fetch active employees with specific attendance type
    employees = frappe.get_all('Employee', filters={'employee_status': 'Active', 'attendance_type': 'Head Office'},
                               fields=['name', 'personal_email', 'company_email', 'prefered_contact_email'])
    
    # Validate if employees were fetched
    if not employees:
        frappe.log_error("No active employees found with the specified attendance type.", "Employee Checkin Report")
        return

    today = getdate(nowdate())
    start_date = f"{add_days(today, -2)} 00:00:00"
    end_date = f"{today} 23:59:59"

    for employee in employees:
        # Fetch checkins for the current employee
        checkins = fetch_checkins(employee.name, start_date, end_date)
        
        # Validate if checkins were fetched
        if not checkins:
            frappe.log_error(f"No checkins found for employee {employee.name} between {start_date} and {end_date}.", "Employee Checkin Report")
            continue
        
        # Generate the report HTML content
        try:
            html_content = generate_report_html(checkins, employee.name)
        except Exception as e:
            frappe.log_error(f"Error generating HTML report for employee {employee.name}: {e}", "Employee Checkin Report")
            continue

        # Save the report to a temporary file
        filename = f"{employee.name}_Checkin_Report.xls"

        # Fetch the appropriate email based on preferred contact
        email = frappe.db.get_value('User', employee.company_email if employee.prefered_contact_email == 'Company Email' else employee.personal_email, 'email')
        
        # Validate the fetched email
        if not email:
            frappe.log_error(f"No valid email found for employee {employee.name}.", "Employee Checkin Report")
            continue
        
        # Send the email with the report
        try:
            frappe.sendmail(
            recipients=email,
            subject="Daily Check-in Report",
            message=html_content
             )
        except Exception as e:
            frappe.log_error(f"Error sending email to {email} for employee {employee.name}: {e}", "Employee Checkin Report")



def send_combined_checkin_report_to_hr(period='daily'):
    start_days = -2 if period == 'daily' else -7
    today = getdate(nowdate())
    start_date = add_days(today, start_days)
    end_date = today

    employees = frappe.get_all('Employee', filters={'status': 'Active'}, fields=['name', 'department'])
    hr_email_info = frappe.get_all('Employee', filters={'designation': 'Hr Executive', 'employee_status': 'Active'}, fields=['personal_email', 'company_email', 'prefered_contact_email'])
    
    if not hr_email_info:
        return

    hr_email = frappe.db.get_value('User', hr_email_info[0].company_email if hr_email_info[0].prefered_contact_email == 'Company Email' else hr_email_info[0].personal_email, 'email')
    if not hr_email:
        return

    all_checkins = []
    for employee in employees:
        checkins = fetch_checkins(employee.name, start_date, end_date)
        if checkins:
            all_checkins.extend(checkins)

    html_content = generate_report_html(all_checkins)
    filename = f"{'Weekly' if period == 'weekly' else 'Daily'}_Checkin_Report_Last_{-start_days}_Days.xls"
    filepath = save_html_to_tempfile(html_content, filename)

    send_email_with_attachment(hr_email, f"{'Weekly' if period == 'weekly' else 'Daily'} Check-in Report for All Employees", f"Please find attached the check-in report for all employees for the last {-start_days} days.", filepath, filename)


@frappe.whitelist(allow_guest=True)
def send_combined_daily_checkin_report_to_emp():
    send_employee_checkin_report()


@frappe.whitelist(allow_guest=True)
def send_combined_daily_checkin_report_to_hr():
    send_combined_checkin_report_to_hr(period='daily')


@frappe.whitelist(allow_guest=True)
def send_combined_weekly_checkin_report_to_hr():
    send_combined_checkin_report_to_hr(period='weekly')
