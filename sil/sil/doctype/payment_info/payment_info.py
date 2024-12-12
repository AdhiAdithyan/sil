# Copyright (c) 2024, Softland and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PaymentInfo(Document):
	def validate(self):
        # Example validation logic
		if self.mode_of_payment or self.mode_of_payment == "Cash":
			self.chequereference_number
			self.reference_no
            # frappe.log_error(_("Amount must be greater than 0"))
			
        
	pass



# if not self.amount or self.amount <= 0:
        #     frappe.throw(_("Amount must be greater than 0"))
        
        # if not self.customer_name:
        #     frappe.throw(_("Customer Name is required"))