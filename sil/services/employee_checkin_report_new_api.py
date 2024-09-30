import frappe
from frappe.utils import add_days, nowdate, getdate, format_datetime, time_diff_in_hours, get_files_path
import os
from io import BytesIO
from openpyxl import Workbook
import tempfile
from frappe import _
from frappe.exceptions import ValidationError, DoesNotExistError


def convert_hours_to_hms(decimal_hours):
    """Convert decimal hours to hour:min:sec format."""
    total_seconds = int(decimal_hours * 3600)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def fetch_checkins(employee, start_date, end_date):
    """Fetch check-ins for an employee between start and end dates."""
    # return frappe.get_all('Employee Checkin',
    #                       filters={'employee': employee, 'time': ['between', [start_date, end_date]]},
    #                       fields=['employee', 'time', 'log_type'],
    #                       order_by='time asc')
    
    checkins = frappe.get_all('Employee Checkin',
                              filters={'employee': employee, 'time': ['between', [start_date, end_date]]},
                              fields=['employee', 'time', 'log_type'],
                              order_by='time asc')
    
    # Fetch employee details to get the department name
    employee_details = fetch_employee_details(employee)
    
    # Attach department info to each check-in log
    for checkin in checkins:
        checkin['department'] = employee_details.department
        checkin['team'] = employee_details.custom_team
    
    return checkins


def fetch_employee_details(employee_name):
    """Fetch employee details including department and email."""
    return frappe.get_doc('Employee', employee_name)


def fetch_hod_email_by_department(department_name):
    """Fetch HOD email for a given department."""
    hod = frappe.get_all('Employee',
                         filters={'department': department_name, 'custom_hod': 1, 'status': 'Active'},
                         fields=['personal_email', 'company_email', 'prefered_contact_email', 'prefered_email'])
    if hod:
        hod_email = hod[0].company_email if hod[0].prefered_contact_email == 'Company Email' else hod[0].personal_email
        return hod_email
    return None



def calculate_daily_working_hours(logs):
    """Calculate total working hours for a single day based on check-in and check-out logs."""
    total_hours = 0
    checkin_time = None
    
    for log in logs:
        if log['log_type'] == 'IN':
            checkin_time = log['time']
        elif log['log_type'] == 'OUT' and checkin_time:
            total_hours += time_diff_in_hours(log['time'], checkin_time)
            checkin_time = None
    
    return total_hours


def generate_report_html(checkins):
    """Generate HTML content for check-in report, grouped by employee and date."""
    grouped_checkins = {}
    max_logs_per_day = 0
    
    # Group check-ins by employee and date
    for checkin in checkins:
        employee = checkin['employee']
        checkin_date = getdate(checkin['time'])
        
        if employee not in grouped_checkins:
            grouped_checkins[employee] = {}
        
        if checkin_date not in grouped_checkins[employee]:
            grouped_checkins[employee][checkin_date] = []
        
        grouped_checkins[employee][checkin_date].append({
            "Time": format_datetime(checkin['time'], 'HH:mm:ss'),
            "Log Type": checkin['log_type'],
            "Department": checkin['department'],
            "Team": checkin['team']
        })
        
        max_logs_per_day = max(max_logs_per_day, len(grouped_checkins[employee][checkin_date]))

    # HTML generation
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
            <th>Employee</th>
            <th>Date</th>
            <th>Department</th>
            <th>Team</th>
            <th>First Check-in Time</th>
            <th>Last Check-out Time</th>
            <th>Total Working Hours</th>"""
    
    for i in range(1, max_logs_per_day + 1):
        html_content += f"<th>Check-in Detail {i}</th>"
    html_content += "</tr>"

    total_hours = 0

    # Iterate over grouped data and generate table rows
    for employee, checkin_dates in grouped_checkins.items():
        for checkin_date, logs in checkin_dates.items():
            first_checkin = logs[0]['Time'] if logs else ""
            last_checkout = logs[-1]['Time'] if logs else ""
            daily_hours = time_diff_in_hours(logs[-1]['Time'], logs[0]['Time']) if len(logs) >= 2 else 0
            total_hours += daily_hours

            html_content += f"""
            <tr>
                <td>{employee}</td>
                <td>{checkin_date}</td>
                <td>{logs[0]['Department']}</td>
                <td>{logs[0]['Team']}</td>
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
        <td colspan="6">Total Working Hours</td>
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
        with open(filepath, 'rb') as f:
            frappe.sendmail(
                recipients=email,
                subject=subject,
                message=message,
                attachments=[{'fname': filename, 'fcontent': f.read()}]
            )
    except Exception as e:
        frappe.log_error(message=str(e), title="Email Sending Error")
    finally:
        os.remove(filepath)  # Ensure file is removed after sending email

def get_combined_checkin_report_to_hr(period='daily'):
    """Send combined check-in reports to HR."""
    start_days = -2 if period == 'daily' else -7
    today = getdate(nowdate())
    start_date = add_days(today, start_days)
    end_date = today

    employees = frappe.get_all('Employee', filters={'status': 'Active'}, fields=['name', 'department'])
    hr_email_info = frappe.get_all('Employee', filters={'designation': 'Hr Executive', 'status': 'Active'}, fields=['personal_email', 'company_email', 'prefered_contact_email', 'prefered_email'])
    
    # if not hr_email_info:
    #     frappe.log_error(message="No HR Executive found", title="HR Email Not Found")
    #     return

    # hr_email = get_hr_email(hr_email_info[0])  # Assuming only one HR Executive, adjust if necessary

    # if not hr_email:
    #     frappe.log_error(message="HR Executive email not found", title="HR Email Not Found")
    #     return

    all_checkins = []
    for employee in employees:
        checkins = fetch_checkins(employee.name, start_date, end_date)
        if checkins:
            all_checkins.extend(checkins)

    html_content = generate_report_html(all_checkins)
    filename = f"{'Weekly' if period == 'weekly' else 'Daily'}_Checkin_Report_Last_{-start_days}_Days.xls"
    filepath = save_html_to_tempfile(html_content, filename)

    # send_email_with_attachment(hr_email, f"{'Weekly' if period == 'weekly' else 'Daily'} Check-in Report for All Employees", f"Please find attached the check-in report for all employees for the last {-start_days} days.", filepath, filename)
    # Create file attachment
    file_name = filename
    file_data = html_content
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "file_url": "/private/files/" + file_name,
        "is_private": 1,
        "content": file_data
        })
    file_doc.save(ignore_permissions=True)

    # Set the response for file download
    frappe.local.response.filename = file_name
    frappe.local.response.filecontent = file_data
    frappe.local.response.type = "binary"
    frappe.local.response.charset = "utf-8"


def get_personal_checkin_reports_to_employees():
    """Send personal check-in reports to each employee for the last two days."""
    today = getdate(nowdate())
    start_date = add_days(today, -2)
    end_date = today

    employees = frappe.get_all('Employee', filters={'status': 'Active'}, fields=['name', 'personal_email', 'company_email', 'prefered_contact_email', 'prefered_email'])
    
    for employee in employees:
        checkins = fetch_checkins(employee.name, start_date, end_date)
        if checkins:
            html_content = generate_report_html(checkins)#, employee.name)
            filename = f"Checkin_Report_{employee.name}_Last_2_Days.xls"
            filepath = save_html_to_tempfile(html_content, filename)

            # email = get_employee_email(employee)
            # if email:
            #     send_email_with_attachment(email, f"Check-in Report for {employee.name}", f"Please find attached your check-in report for the last two days.", filepath, filename)
           
            # Create file attachment
            file_name = filename
            file_data = html_content
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "file_url": "/private/files/" + file_name,
                "is_private": 1,
                "content": file_data
            })
            file_doc.save(ignore_permissions=True)

            # Set the response for file download
            frappe.local.response.filename = file_name
            frappe.local.response.filecontent = file_data
            frappe.local.response.type = "binary"
            frappe.local.response.charset = "utf-8"
        else:
            pass    
            


def get_department_checkin_report_to_hods():
    """Send department-specific check-in reports to HODs."""
    today = getdate(nowdate())
    start_date = add_days(today, -2)
    end_date = today

    departments = frappe.get_all('Employee', filters={'status': 'Active'}, fields=['department'])
    departments = list(set([dept['department'] for dept in departments if dept['department']]))

    for department in departments:
        employees = frappe.get_all('Employee', filters={'department': department, 'status': 'Active'}, fields=['name'])
        all_checkins = []

        for employee in employees:
            checkins = fetch_checkins(employee.name, start_date, end_date)
            if checkins:
                all_checkins.extend(checkins)

        if all_checkins:
            html_content = generate_report_html(all_checkins)
            filename = f"Department_Checkin_Report_{department}_Last_7_Days.xls"
            filepath = save_html_to_tempfile(html_content, filename)

            # hod_email = fetch_hod_email_by_department(department)
            # if hod_email:
            #     send_email_with_attachment(hod_email, f"Department Check-in Report for {department}", f"Please find attached the check-in report for the {department} department for the last 7 days.", filepath, filename)

            # Create file attachment
            file_name = filename
            file_data = html_content
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "file_url": "/private/files/" + file_name,
                "is_private": 1,
                "content": file_data
            })
            file_doc.save(ignore_permissions=True)

            # Set the response for file download
            frappe.local.response.filename = file_name
            frappe.local.response.filecontent = file_data
            frappe.local.response.type = "binary"
            frappe.local.response.charset = "utf-8"




@frappe.whitelist(allow_guest=True)
def get_department_checkin_reports():
    get_department_checkin_report_to_hods()


@frappe.whitelist(allow_guest=True)
def get_daily_checkin_report_to_hr():
    get_combined_checkin_report_to_hr(period='daily')


@frappe.whitelist(allow_guest=True)
def get_weekly_checkin_report_to_hr():
    get_combined_checkin_report_to_hr(period='weekly')


@frappe.whitelist(allow_guest=True)
def get_personal_checkin_reports_mail():
    get_personal_checkin_reports_to_employees()


def get_hr_email(hr_email_info):
    """Retrieve HR email address based on preference."""
    if hr_email_info.prefered_contact_email == 'Company Email':
        return hr_email_info.company_email
    elif hr_email_info.prefered_contact_email == 'Personal Email':
        return hr_email_info.personal_email
    elif hr_email_info.prefered_contact_email == 'User ID':
        return hr_email_info.prefered_email
    return None


def get_employee_email(employee):
    """Retrieve employee email address based on preference."""
    if employee.prefered_contact_email == 'Company Email':
        return employee.company_email
    elif employee.prefered_contact_email == 'Personal Email':
        return employee.personal_email
    elif employee.prefered_contact_email == 'User ID':
        return employee.prefered_email
    return None
    
