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
    """Convert a date string from 'dd-mm-yyyy' to 'yyyy-mm-dd' format."""
    print(f"convertDateStringToDateTime: {dateString}")
    input_date_str = str(dateString)
    try:
        # Parse the date string to a datetime object
        date_object = datetime.strptime(input_date_str, "%d-%m-%Y")
        # Format the date object to the desired output format
        output_date_str = date_object.strftime("%Y-%m-%d")
    except Exception as e:
        frappe.log_error(f"Error converting date string: {str(e)}", "Date Conversion Error")
        output_date_str = input_date_str  # Default fallback to the input string
    return output_date_str


def convert_hours_to_hms(decimal_hours):
    """Convert decimal hours to hour:min:sec format."""
    if decimal_hours is None:
        frappe.log_error("Decimal hours value is None.", "Convert Hours Error")
        return "00:00:00"
    
    try:
        total_seconds = int(decimal_hours * 3600)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        frappe.log_error(f"Error converting hours to HMS: {str(e)}", "Convert Hours Error")
        return "00:00:00"


def calculate_daily_working_hours(logs):
    """Calculate total working hours for a single day based on check-in and check-out logs."""
    total_hours = 0
    checkin_time = None
    try:
        for log in logs:
            if log.get('log_type') == 'IN':
                checkin_time = log['time']
            elif log.get('log_type') == 'OUT' and checkin_time:
                total_hours += time_diff_in_hours(log['time'], checkin_time)
                checkin_time = None
    except Exception as e:
        frappe.log_error(f"Error calculating daily working hours: {str(e)}", "Working Hours Calculation Error")
    return total_hours


def fetch_employee_details(employee_name):
    """Fetch employee details including department and email."""
    try:
        if not employee_name:
            raise ValidationError("Employee name is required.")
        
        return frappe.get_doc('Employee', employee_name)
    except DoesNotExistError:
        frappe.log_error(f"Employee {employee_name} does not exist.", "Fetch Employee Error")
    except ValidationError as ve:
        frappe.log_error(f"Validation Error: {str(ve)}", "Fetch Employee Validation Error")
    except Exception as e:
        frappe.log_error(f"Error fetching employee details: {str(e)}", "Fetch Employee Error")
    return None


@frappe.whitelist()
def get_combined_checkin_report_to_hr(employee_name=None, team=None, department=None, from_date=None, to_date=None):
    # Initialize your response dictionary
    response = {
        'status': 'error',
        'message': '',
        'file_url': ''
    }

    try:
        # Validate required fields
        if not from_date or not to_date:
            response['message'] = 'From Date and To Date are required.'
            return response

        # Validate date inputs if provided
        from_date = getdate(from_date)
        to_date = getdate(to_date)
        if from_date > to_date:
            response['message'] = 'From Date cannot be greater than To Date.'
            return response

        # Fetch check-in records based on filters
        filters = {}

        # Apply filters based on provided parameters
        if employee_name:
            filters['employee'] = employee_name
        if from_date:
            filters['time'] = [">=", from_date]
        if to_date:
            filters['time'] = ["<=", to_date]

        # Fetch data based on filters
        checkins = frappe.get_all(
            'Employee Checkin',
            filters=filters,
            fields=['employee', 'time', 'log_type'],
            order_by='time asc'
        )

        if not checkins:
            response['message'] = 'No check-in records found for the provided filters.'
            return response

        # If employee_name is None, fetch all employee details
        if not employee_name:
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
            if not employee_details:
                response['message'] = 'Employee details not found.'
                return response

            # Attach department info to each check-in log
            for checkin in checkins:
                checkin['department'] = employee_details.department
                checkin['team'] = employee_details.custom_team

        # Logic to generate the report
        file_path = generate_excel_report(checkins)

        if file_path:
            response['status'] = 'success'
            response['file_url'] = file_path  # The URL or path to the generated file
        else:
            response['message'] = 'Failed to generate report.'

        print(f"response :{response}")    
    except ValidationError as ve:
        print(f"Validation Error: {str(ve)}")
        frappe.log_error(f"Validation Error: {str(ve)}", "Check-in Report Validation Error")
        response['message'] = f"Validation Error: {str(ve)}"
    except Exception as e:
        print(f"Error generating check-in report: {str(e)}")
        frappe.log_error(f"Error generating check-in report: {str(e)}", "Check-in Report Generation Error")
        response['message'] = 'An unexpected error occurred while generating the report.'

    return response


def generate_excel_report(checkins):
    try:
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
                    <td>{convert_hours_to_hms(daily_hours)}</td>
                """
                for log in logs:
                    html_content += f"<td>{log['Time']} ({log['Log Type']})</td>"
                html_content += "</tr>"

        html_content += """
            </table>
        </body>
        </html>
        """

        # Convert HTML to Excel
        file_name = "checkin_report.xls"
        # file_url = save_file(file_name, BytesIO(html_content.encode()), None, content_type='application/vnd.ms-excel')
        file_url = save_file(file_name, html_content, "Shift Type", "Shift Type", folder="Home", is_private=True)
        return file_url.file_url

    except Exception as e:
        print(f"Error generating Excel report: {str(e)}")
        frappe.log_error(f"Error generating Excel report: {str(e)}", "Generate Excel Report Error")
        return None
