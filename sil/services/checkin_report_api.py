import frappe
from io import BytesIO
from frappe.utils import (
    get_url,
    getdate,
    format_datetime,
    time_diff_in_hours,
    get_files_path,
)
from frappe.utils.file_manager import save_file
from datetime import datetime,timedelta
from frappe.exceptions import ValidationError, DoesNotExistError

def convertDateStringToDateTime(dateString):
    """Convert a date string from 'dd-mm-yyyy' to 'yyyy-mm-dd' format."""
    input_date_str = str(dateString)
    try:
        date_object = datetime.strptime(input_date_str, "%d-%m-%Y")
        return date_object.strftime("%Y-%m-%d")
    except Exception as e:
        frappe.log_error(f"Error converting date string: {str(e)}", "Date Conversion Error")
        return input_date_str  # Return original string on error

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
    # print("calculate_daily_working_hours:")
    # print(logs)
    try:
        for log in logs:
            if log.get('Log Type') == 'IN':
                checkin_time = log['Time']
            elif log.get('Log Type') == 'OUT' and checkin_time:
                # print("checkin_time")
                # print(checkin_time)
                # print("log['time']")
                # print(log['Time'])
                total_hours += time_diff_in_hours(log['Time'], checkin_time)
                checkin_time = None
    except Exception as e:
        frappe.log_error(f"Error calculating daily working hours: {str(e)}", "Working Hours Calculation Error")
    return total_hours


# def calculate_daily_working_hours(logs):
#     """
#     Calculate total working hours for a single day based on check-in and check-out logs.
    
#     :param logs: List of log entries containing 'time' and 'log_type'.
#     :return: Total working hours as a float.
#     """
#     total_working_time = timedelta()  # Store total working time as a timedelta object
#     checkin_time = None  # To track the last check-in time
#     print("calculate_daily_working_hours:")
#     print(logs)
#     try:
#         # Iterate through each log entry
#         for log in logs:
#             log_time = datetime.strptime(log['time'], '%H:%M:%S')  # Convert string to datetime object
#             print("calculate_daily_working_hours: log: log_time")
#             print(log_time)

#             if log.get('log_type') == 'IN':
#                 # Update check-in time
#                 checkin_time = log_time
#             elif log.get('log_type') == 'OUT' and checkin_time:
#                 # Calculate the time difference if there is a valid check-in
#                 working_time = log_time - checkin_time
#                 total_working_time += working_time
#                 checkin_time = None  # Reset check-in time after processing the pair

#     except Exception as e:
#         frappe.log_error(f"Error calculating daily working hours: {str(e)}", "Working Hours Calculation Error")

#     # Return total working hours as a float (in hours)
#     return total_working_time.total_seconds() / 3600



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
def get_combined_checkin_report_to_hr(employee_name=None, from_date=None, to_date=None):
    """Get combined check-in report to HR."""
    response = {
        'status': 'error',
        'message': '',
        'file_url': ''
    }

    try:
        if not from_date or not to_date:
            response['message'] = 'From Date and To Date are required.'
            return response

        from_date = getdate(from_date)
        to_date = getdate(to_date)

        if from_date > to_date:
            response['message'] = 'From Date cannot be greater than To Date.'
            return response

        filters = {}
        if employee_name:
            filters['employee'] = employee_name
        filters['time'] = [">=", from_date, "<=", to_date]

        checkins = frappe.get_all(
            'Employee Checkin',
            filters=filters,
            fields=['employee', 'time', 'log_type'],
            order_by='time asc'
        )

        if not checkins:
            response['message'] = 'No check-in records found for the provided filters.'
            return response

        if not employee_name:
            all_employees = frappe.get_all('Employee', fields=['name', 'department', 'custom_team'])
            employee_details_map = {emp['name']: emp for emp in all_employees}

            for checkin in checkins:
                employee_detail = employee_details_map.get(checkin['employee'], {})
                checkin['department'] = employee_detail.get('department', '')
                checkin['team'] = employee_detail.get('custom_team', '')
        else:
            employee_details = fetch_employee_details(employee_name)
            if not employee_details:
                response['message'] = 'Employee details not found.'
                return response

            for checkin in checkins:
                checkin['department'] = employee_details.department
                checkin['team'] = employee_details.custom_team

        file_path = generate_excel_report(checkins)

        if file_path:
            response['status'] = 'success'
            response['file_url'] = file_path
        else:
            response['message'] = 'Failed to generate report.'

    except ValidationError as ve:
        frappe.log_error(f"Validation Error: {str(ve)}", "Check-in Report Validation Error")
        response['message'] = f"Validation Error: {str(ve)}"
    except Exception as e:
        frappe.log_error(f"Error generating check-in report: {str(e)}", "Check-in Report Generation Error")
        response['message'] = 'An unexpected error occurred while generating the report.'

    return response

def generate_excel_report(checkins):
    """Generate an Excel report from check-in data."""
    try:
        grouped_checkins = {}
        max_logs_per_day = 0

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
                "Department": checkin.get('department', ''),
                "Team": checkin.get('team', '')
            })

            max_logs_per_day = max(max_logs_per_day, len(grouped_checkins[employee][checkin_date]))

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
                    <th colspan="7"><h2>Check-In Report</h2></th>
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

        for i in range(1, max_logs_per_day + 1):
            html_content += f"<th>Check-in Detail {i}</th>"
        html_content += "</tr>"

        total_hours = 0

        # Iterate through grouped check-ins to process each employee's logs
        for employee, checkin_dates in grouped_checkins.items():
            for checkin_date, logs in checkin_dates.items():
                # Use a set to track unique logs based on Time and Log Type
                unique_logs = []
                seen_logs = set()
                time_diff=calculate_daily_working_hours(logs)
                print(f"Total Working Hours: {time_diff:.2f}")
                print("Time Difference:")
                print(time_diff)
                # time_diff=convert_hours_to_hms(time_diff)
                # print(time_diff)
                for log in logs:
                    log_identifier = (log['Time'], log['Log Type'])  # Create a unique identifier

                    if log_identifier not in seen_logs:
                        seen_logs.add(log_identifier)
                        unique_logs.append(log)  # Keep the unique log

                print("unique_logs:")
                print(unique_logs)
                # Process unique logs
                first_checkin = unique_logs[0]['Time'] if unique_logs else ""
                last_checkout = unique_logs[-1]['Time'] if unique_logs else ""
                # for i in unique_logs:
                #     print(f"unique_logs : {i['Time']}")

                # daily_hours = time_diff_in_hours(last_checkout, first_checkin) if len(unique_logs) >= 2 else 0
                # total_hours += daily_hours
                daily_hours = time_diff
                total_hours += daily_hours

                html_content += f"""
                <tr>
                    <td>{employee}</td>
                    <td>{checkin_date}</td>
                    <td>{unique_logs[0]['Department']}</td>
                    <td>{unique_logs[0]['Team']}</td>
                    <td>{first_checkin}</td>
                    <td>{last_checkout}</td>
                    <td>{convert_hours_to_hms(daily_hours)}</td>
                """
                for log in unique_logs:
                    html_content += f"<td>{log['Time']} ({log['Log Type']})</td>"
                html_content += "</tr>"

        html_content += """
            </table>
        </body>
        </html>
        """

        file_name = "checkin_report.xls"
        file_url = save_file(file_name, html_content, "Shift Type", "Shift Type", folder="Home", is_private=True)
        return file_url.file_url

    except Exception as e:
        frappe.log_error(f"Error generating Excel report: {str(e)}", "Excel Report Generation Error")
        return None
