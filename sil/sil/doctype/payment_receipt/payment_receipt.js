// Copyright (c) 2024, Softland and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Payment Receipt", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Payment Receipt', {
    on_submit(frm) {
        // Validate main document fields
        // let is_main_doc_valid = true;
        let {payment_type,mode_of_payment}=frm.doc
        frappe.call({
            method:"sil.services.",
            args:{
                "payment_type":payment_type,
                "mode_of_payment":mode_of_payment
            }

        });
        

    }
});    