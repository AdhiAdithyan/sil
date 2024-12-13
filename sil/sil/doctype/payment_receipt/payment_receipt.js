// Copyright (c) 2024, Softland and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Payment Receipt", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Payment Receipt', {
    on_submit: function(frm) {
        // Validate main document fields
        let { payment_type, mode_of_payment } = frm.doc;
        if (payment_type && mode_of_payment) {
            frappe.call({
                method: "sil.services.payment_receipt_api.validate_payment",
                args: {
                    "payment_type": payment_type,
                    "mode_of_payment": mode_of_payment
                },
                callback: function(r) {
                    if (r.message) {
                        // Handle validation result
                    }
                }
            });
        } else {
            frappe.msgprint("Please select payment type and mode of payment");
        }
    }
});