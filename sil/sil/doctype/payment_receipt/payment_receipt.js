// Copyright (c) 2024, Softland and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Payment Receipt", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Payment Receipt', {
    on_submit: function(frm) {
        // Validate main document fields
        const requiredFields = ['payment_type', 'mode_of_payment'];
        const missingFields = requiredFields.filter(field => !frm.doc[field]);

        if (missingFields.length) {
            frappe.msgprint(`Please select ${missingFields.join(', ')}`);
            return;
        }

        //Create EMPLOYEE ADVANCE AND PAYMENT ENTRY for it.
        // Execute only if custom_is_employee_liability is 1
        if (frm.doc.custom_is_employee_liability === 1) {
            let total_paid_amount = 0;
            
            // Ensure necessary values are present before calling the function
            if (!frm.doc.executive || !frm.doc.account_paid_to || total_paid_amount <= 0) {
                frappe.msgprint(__('Missing required fields or invalid paid amount.'));
                return;
            }
        
            // Debug log to check remark value
            console.log("Full frm.doc:", frm.doc);
        
            
            console.log("Final remark value being sent:", frm.doc.custom_info_remarks);
        
            frappe.call({
                method: "sil.services.payment_receipt_api.payment_entry_for_employee_liability",
                args: {
                    executive_name: frm.doc.executive,
                    paid_amount: total_paid_amount,
                    amount_paid_from: frm.doc.account_paid_to,
                    receipt_number: frm.doc.name || '', // Default to empty string if not set
                    reference_number: frm.doc.reference_number || '',
                    cheque_reference_date: frm.doc.chequereference_date || '',
                    remark: frm.doc.custom_info_remarks
                },
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.msgprint(__(r.message.message));
                        console.log("API Response:", r.message);
                    } else {
                        frappe.msgprint(__("Error: " + (r.message.message || "Unknown error")));
                        console.log("API Error Response:", r.message);
                    }
                }
            });
        }

        // const data = {
        //     payment_type: frm.doc.payment_type || '', // Default to empty string if not set
        //     mode_of_payment: frm.doc.mode_of_payment || '', // Default to empty string if not set
        //     payment_entry_details: frm.doc.payment_entry_details || [], // Default to empty array if not set
        //     executive: frm.doc.executive || '', // Default to empty string if not set
        //     bank_account: frm.doc.bank_account || '', // Default to empty string if not set
        //     account_paid_to: frm.doc.account_paid_to || '', // Default to empty string if not set
        //     receipt_number: frm.doc.receipt_number || '', // Default to empty string if not set
        //     account_paid_from: frm.doc.account_paid_from || '', // Default to empty string if not set
        //     amount_received: frm.doc.amount_received || 0, // Default to 0 if not set
        // };

        frappe.call({
            method: "sil.services.payment_receipt_api.getAllReceiptDetailsFromDoc",
            args: {
                payment_type: frm.doc.payment_type || '', // Default to empty string if not set
                mode_of_payment: frm.doc.mode_of_payment || '', // Default to empty string if not set
                payment_entry_details: frm.doc.payment_entry_details || [], // Default to empty array if not set
                executive: frm.doc.executive || '', // Default to empty string if not set
                bank_account: frm.doc.bank_account || '', // Default to empty string if not set
                account_paid_to: frm.doc.account_paid_to || '', // Default to empty string if not set
                receipt_number: frm.doc.receipt_number || '', // Default to empty string if not set
                custom_deposited_by_customer: frm.doc.custom_deposited_by_customer || '', // Default to empty string if not set
                amount_received: frm.doc.amount_received || 0, // Default to 0 if not set
                amount_paid:frm.doc.amount_paid || 0,
                reference_number:frm.doc.reference_number || '',
                chequereference_date:frm.doc.chequereference_date || '',
                account_paid_from:frm.doc.account_paid_from || '',
                custom_is_suspense_entry:frm.doc.custom_is_suspense_entry || false
            },
            callback: function(r) {
                if (r.message) {
                    // Handle validation result
                }
            }
        });
    }
});