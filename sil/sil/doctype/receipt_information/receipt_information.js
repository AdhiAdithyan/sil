// Copyright (c) 2024, Softland and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Receipt Information", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Receipt Information', {
    
    validate(frm) {

          // Validate main document fields
          let is_main_doc_valid = true;
        
          // Example validations for main document fields
          if (!frm.doc.account) {
              frappe.msgprint(__('Account is required.'));
              is_main_doc_valid = false;
          }
         
        //   if (!frm.doc.custom_company) {
        //     frappe.msgprint(__('Company is required.'));
        //     is_main_doc_valid = false;
        // }
        //   currently not required
        //   if (!frm.doc.executive) {
        //       frappe.msgprint(__('Executive is required.'));
        //       is_main_doc_valid = false;
        //   }
          
        //   if (!frm.doc.bank_account) {
        //       frappe.msgprint(__('Bank account is required.'));
        //       is_main_doc_valid = false;
        //   }
          
        //   if (!frm.doc.mode_of_payment) {
        //       frappe.msgprint(__('Mode of payment is required.'));
        //       is_main_doc_valid = false;
        //   }
          
        //   if (!frm.doc.date) {
        //       frappe.msgprint(__('Date is required.'));
        //       is_main_doc_valid = false;
        //   }
          
          if (!frm.doc.amount || parseFloat(frm.doc.amount) <= 0) {
              frappe.msgprint(__('Amount should be greater than zero.'));
              is_main_doc_valid = false;
          }
  
          // If main document validation fails, prevent saving the form
          if (!is_main_doc_valid) {
              frappe.validated = false;
              return;
          }
          
        // Check if customer table has at least one item
        if (!frm.doc.customer || frm.doc.customer.length === 0) {
            frappe.msgprint(__('Please add at least one entry before proceeding'));
            return;
        }
        // Check if entries table has at least one item
        if (!frm.doc.entries || frm.doc.entries.length === 0) {
            frappe.msgprint(__('Please add at least one outstanding entry before proceeding'));
            return;
        }
        // Validate each row in the customer table
        let is_cust_valid = true;
        let seen = new Set(); // To track seen combinations of customer and type
        frm.doc.customer.forEach(row => {
            if (!row.customer || !row.type) {
                is_cust_valid = false;
                return false; // Exit forEach loop early
            }

            let key = row.customer + '-' + row.type;
            if (seen.has(key)) {
                is_cust_valid = false;
                return false; // Exit forEach loop early
            } else {
                seen.add(key);
            }
        });

        if (!is_cust_valid) {
            frappe.msgprint(__('Customer and Type fields must be filled uniquely for each row'));
            return;
        }

        // Iterate over entries and validate the amount
        let is_entry_valid = true;
        frm.doc.entries.forEach(entry => {
            if (parseFloat(entry.amount) <= 0) {
                is_entry_valid = false;
                frappe.msgprint({
                    title: __('Validation Error'),
                    indicator: 'red',
                    message: __('Entry {0} has an amount of {1}, which is not greater than zero.', [entry.name, entry.amount])
                });
            }
        });

          // Iterate over entries and validate the amount
          let total_amount = 0;
  
          frm.doc.entries.forEach(entry => {
              let entry_amount = parseFloat(entry.amount);
              if (entry_amount <= 0) {
                  is_entry_valid = false;
                  frappe.msgprint({
                      title: __('Validation Error'),
                      indicator: 'red',
                      message: __('Entry {0} has an amount of {1} for the given {2}, which is not greater than zero.', [entry.customer, entry.amount,enrty.type])
                  });
              }
              total_amount += entry_amount;
          });
  
          // Check if the sum of entry amounts equals the main document amount
          if (total_amount !== parseFloat(frm.doc.amount)) {
              frappe.msgprint({
                  title: __('Validation Error'),
                  indicator: 'red',
                  message: __('The total amount of entries ({0}) does not equal the main document amount ({1}).', [total_amount, frm.doc.amount])
              });
              frappe.validated = false;
              return;
          }

        let formData = {
            main_document: {
                    doctype: frm.doc.doctype,
                    status: frm.doc.status,
                    naming_series: frm.doc.naming_series,
                    company:frm.doc.custom_company,
                    account: frm.doc.account,
                    executive: frm.doc.executive,
                    bank_account: frm.doc.bank_account,
                    mode_of_payment: frm.doc.mode_of_payment,
                    date: frm.doc.date,
                    amount: frm.doc.amount
            },
            child_tables: {
                customer: frm.doc.customer,  // child table name
                entries: frm.doc.entries  // child table name
            }
        }
        console.log("Custom button clicked123456789");

          // Show the progress dialog
          frappe.msgprint({
            message: __("Processing... Please wait."),
            indicator: 'blue',
            title: __("Processing")
        });
// If all entries are valid, proceed with the frappe.call
if (is_cust_valid && is_entry_valid) {
        frappe.call({
            method: 'sil.services.paymentDetails.paymentEntry', // Path to your method
            args: {
                frm: frm.doc, // Pass the document data
                formData: JSON.stringify(formData, null, 2)
            },
            callback: function(response) {
                // Handle the response here
                console.log(response.message);
                // Hide the progress dialog
                frappe.hide_msgprint();
                if (response.message) {
                    // Handle successful response
                    console.log("Received from server:", response.message.message);
                } else {
                    // Handle error or empty response
                    console.log("No response from server or error occurred.");
                }
            } ,
            error: function(error) {
                // Hide the progress dialog in case of error
                frappe.hide_msgprint();
                
                // Handle the error
                console.error("An error occurred:", error);
            }
        });
    } else {
        // Prevent form from being saved if validation fails
        frappe.validated = false;
    }
    }
});