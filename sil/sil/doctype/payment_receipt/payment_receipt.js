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