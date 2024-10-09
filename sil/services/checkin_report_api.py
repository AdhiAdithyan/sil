import frappe
import os
from io import BytesIO
from frappe.utils import (
    get_url,
    getdate,
    add_days,
    nowdate,
    format_datetime,
    time_diff_in_hours,
    get_files_path,
)
from frappe.utils.file_manager import save_file
from datetime import datetime
from frappe.exceptions import ValidationError, DoesNotExistError



def convertDateStringToDateTime(dateString):
    """Convert a date string from 'dd-mm-yyyy' to 'yyyy-mm-dd HH:MM:SS.000000' format."""
    print(f"convertDateStringToDateTime: {dateString}")
    input_date_str = str(dateString)
    try:
        # Parse the date string to a datetime object
        date_object = datetime.strptime(input_date_str, "%d-%m-%Y")
        # Format the date object to the desired output format
        output_date_str = date_object.strftime("%Y-%m-%d")
    except Exception as e:
        # If parsing fails, return a default datetime
        output_date_str = input_date_str
    
    return output_date_str  # Return the formatted date string


def convert_hours_to_hms(decimal_hours):
    """Convert decimal hours to hour:min:sec format."""
    total_seconds = int(decimal_hours * 3600)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


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


def fetch_employee_details(employee_name):
    """Fetch employee details including department and email."""
    if employee_name:
        return frappe.get_doc('Employee', employee_name)
        

@frappe.whitelist()
def get_combined_checkin_report_to_hr(employee_name=None, team=None, department=None, from_date=None, to_date=None):
    # Initialize your response dictionary
    response = {
        'status': 'error',
        'message': '',
        'file_url': ''
    }


    # Validate date inputs if provided
    if from_date and to_date:
        from_date = getdate(from_date)
        to_date = getdate(to_date)
        if from_date > to_date:
            response['message'] = 'From Date cannot be greater than To Date.'
            return response
    
    # Fetch check-in records based on filters
    filters = {
        # 'docstatus': 1  # Assuming docstatus = 1 for submitted records
    }
    
    # Apply filters based on provided parameters
    if employee_name:
        filters['employee'] = employee_name
    if from_date:
        from_date = convertDateStringToDateTime(from_date)
        filters['time'] = [">=", from_date]
    if to_date:
        to_date = convertDateStringToDateTime(to_date)
        filters['time'] = ["<=", to_date]
    
    # Fetch data based on filters
    checkins = frappe.get_all(
        'Employee Checkin',
        filters=filters,
        fields=['employee', 'time', 'log_type'],
        order_by='time asc'
    )

    print(f"from_date: {from_date}")
    print(f"to_date: {to_date}")
    print(f"checkins: {checkins}")
    print(f"filters: {filters}")

    # If employee_name is None, fetch all employee details
    if employee_name is None:
        all_employees = frappe.get_all('Employee', fields=['name', 'department', 'custom_team'])
        employee_details_map = {emp['name']: emp for emp in all_employees}
        
        # Attach department info to each check-in log
        for checkin in checkins:
            employee_detail = employee_details_map.get(checkin['employee'], {})
            checkin['department'] = employee_detail.get('department', '')
            checkin['team'] = employee_detail.get('custom_team', '')
    else:
        # Fetch employee details to get the department name
        employee_details = fetch_employee_details(employee_name)

        # Attach department info to each check-in log
        for checkin in checkins:
            checkin['department'] = employee_details.department
            checkin['team'] = employee_details.custom_team

    # Logic to generate the report
    if not checkins:
        response['message'] = 'No records found for the selected filters.'
        return response

    print(f"checkins details: {checkins}")

    # Your logic to compile data into an Excel file
    file_path = generate_excel_report(checkins)
    
    if file_path:
        print(f"file_path: {file_path}")
        response['status'] = 'success'
        response['file_url'] = file_path  # The URL or path to the generated file
    else:
        response['message'] = 'Failed to generate report.'

    # if send_report_via_email(file_path):    
    #     response['message'] = 'Report generated and sent via email.'
    
    print(f"get_combined_checkin_report_to_hr response: {response}")
    return response


def generate_excel_report(checkins):
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
    
    # Create an HTML string for the Excel file
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #000;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        
        <table>
            <tr>
                <th colspan="5"><h2>Check-In Report</h2></th>
            </tr>
            <tr>
                <th>Employee</th>
                <th>Date</th>
                <th>Department</th>
                <th>Team</th>
                <th>First Check-in Time</th>
                <th>Last Check-out Time</th>
                <th>Total Working Hours</th>
    """

    # Add dynamic header for check-in details
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

            # Populate the table with check-in data
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
            <tr>
                <td colspan="6">Total Working Hours</td>
                <td>{convert_hours_to_hms(total_hours)}</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Save HTML to an Excel file (XLS format)
    xls_file_path = save_html_to_excel(html_content)
    return xls_file_path


def save_html_to_excel(html_content):
    """Save the generated HTML content as an Excel file."""
    # Generate file name based on current date
    file_name = f"Checkin_Report_{nowdate()}.xlsx"
    file_path = os.path.join(get_files_path(), file_name)
    
    try:
        with open(file_path, 'w') as file:
            file.write(html_content)
    except Exception as e:
        frappe.log_error(f"Error saving Excel file: {str(e)}")
        return None
    
    print(f"file_path :{file_path}")
    return file_path




def send_report_via_email(file_path):
    """Send the generated report via email."""
    # Replace with actual HR email address or fetch it dynamically
    hr_email = "adithyans@windrolinx.com"  # Update this with the appropriate email logic

    # Prepare the email content
    subject = "Check-In Report"
    message = "Please find attached the Check-In Report for the requested period."

    print(f"Sending email to {hr_email} with attachment: {file_path}")  # Debug statement

    try:
        # Check the parameters being passed
        print(f"Recipients: {[hr_email]}, Subject: {subject}, Message: {message}, Attachments: {[file_path]}")

        frappe.sendmail(
            recipients=hr_email,
            subject=subject,
            message=message,
            attachments=file_path  # Attach the generated Excel file
        )
        print(f"Email sent to {hr_email} with attachment {file_path}.")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        frappe.log_error(f"Error sending email: {str(e)}")
        return False
