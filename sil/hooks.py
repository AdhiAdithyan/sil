# import frappe
# from packaging import version


# def check_app_versions():
#     app_versions = {
#         "chat": "0.0.1",
#         "erpnext": "15.38.2",
#         "frappe": "15.44.1",
#         "hrms": "16.0.0-dev",
#         "payments": "0.0.1"
#     }

#     for app, req_version in app_versions.items():
#         if app in frappe.get_installed_apps():
#             installed_version = frappe.get_app_version(app)
#             if version.parse(installed_version) < version.parse(req_version):
#                 frappe.throw(f"{app} version must be >= {req_version}. Installed: {installed_version}")

app_name = "sil"
app_title = "sil"
app_publisher = "Softland"
app_description = "Billing Solution"
app_email = "admin@softlandindia.co.in"
app_license = "mit"

# required_apps = ["chat","frappe","erpnext","hrms","payments"]  # Add more apps as needed
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sil/css/sil.css"
# app_include_js = "/assets/sil/js/sil.js"

# include js, css files in header of web template
# web_include_css = "/assets/sil/css/sil.css"
# web_include_js = "/assets/sil/js/sil.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sil/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sil/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sil.utils.jinja_methods",
# 	"filters": "sil.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sil.install.before_install"
# after_install = "sil.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sil.uninstall.before_uninstall"
# after_uninstall = "sil.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sil.utils.before_app_install"
# after_app_install = "sil.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sil.utils.before_app_uninstall"
# after_app_uninstall = "sil.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sil.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sil.tasks.all"
# 	],
# 	"daily": [
# 		"sil.tasks.daily"
# 	],
# 	"hourly": [
# 		"sil.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sil.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sil.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sil.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sil.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sil.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sil.utils.before_request"]
# after_request = ["sil.utils.after_request"]

# Job Events
# ----------
# before_job = ["sil.utils.before_job"]
# after_job = ["sil.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sil.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs

# }
# scheduler_events = {
#     "weekly": [
#         "sil.services.rest.sentWeeklyMailToHR"
#     ],

#      "daily": [
#         "sil.services.rest.sentMailToEmp",
#         "sil.services.rest.sentDailyMailToHR"
#     ],
# }

doc_events = {
    "Sales Invoice": {
        "on_submit": "sil.services.sales_order_api.updateItemFamilySerialNoList"
    }
}



# scheduler_events = {
#     "cron": {
        # "0 10 * * *": [
        #     "sil.services.employee_checkin_report_new_api.generate_and_send_daily_and_last_day_report",
        #     "sil.services.employee_checkin_report_new_api.generate_and_send_team_reports"
        # ],
#         "0 10 * * 1": [  # Executes every Monday at 10:00
#             "sil.services.employee_checkin_report_new_api.get_weekly_checkin_report_to_hr"
#         ]
#     }
# }

# Trigger this function after installation
after_install = check_app_versions

fixtures = [
    "Client Script",
    "Server Script",
    "Custom Field",
    "Property Setter",
    "Print Format",
    "DocType",
    "Report",
    "Letter Head",
    "Workflow",
    "Workflow State",
    "Workflow Action",
    "Workflow Action Master",
    # Additional fields
    {"dt": "Custom DocPerm"},
    {"dt": "Role"},
    {"dt": "Custom Role"},
    {"dt": "Module Def"},
    {"dt": "Translation"},
    {"dt": "Portal Menu Item"},
    {"dt": "Web Page"},
    {"dt": "Web Form"},
    {"dt": "Notification"},
    # {"dt": "Email Alert"},
    {"dt": "Email Template"},
    #{"dt": "Dashboard"},
     {"dt": "Dashboard",
        "filters": [["is_standard", "=", "0"]],
        "ignore_version": 1},
    {"dt": "Dashboard Chart"},
    {"dt": "User Permission"}
]




