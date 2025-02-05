frappe.ui.form.on('Payment Intimation', {
    validate(frm) {
        let is_main_doc_valid = true;
        let is_cust_valid = true;
        let is_entry_valid = true;

        // Validate mode of payment
        if (frm.doc.mode_of_payment !== 'Cash') {
            if (!frm.doc.chequereference_number) {
                frappe.msgprint(__('Please fill the Cheque Reference Number'));
                frappe.validated = false;
            }
            if (!frm.doc.reference_no) {
                frappe.msgprint(__('Please fill the Reference No'));
                frappe.validated = false;
            }
        } 
        if (frm.doc.mode_of_payment === 'Cash')  {
            frm.set_value('chequereference_number', '');
            frm.set_value('reference_no', '');
            frm.set_df_property('chequereference_number', 'reqd', 0);
            frm.set_df_property('reference_no', 'reqd', 0);
            if (!frm.doc.chequereference_number || !frm.doc.reference_no) {
                frappe.validated = true;
                }
        }
        
        if (frm.doc.unallocated_amount > 0) {
            frappe.validated = false; // Prevent immediate save
            let formattedAmount = parseFloat(frm.doc.unallocated_amount).toFixed(2);
        
            // Construct message
            let message = `<p>Allocate amount <b>₹${formattedAmount}</b> to Executive <b>${frm.doc.executive}</b>?</p>`;
            
            // Create and show dialog
            let d = new frappe.ui.Dialog({
                title: 'Unallocated Amount',
                fields: [
                    {
                       
                        fieldname: 'message',
                        fieldtype: 'HTML',
                        options: message
                    }
                ],
                primary_action_label: 'Yes',
                secondary_action_label: 'No',
                primary_action() {
                    let remainingUnallocated = frm.doc.unallocated_amount;
                    let receipt_entry = frm.doc.receipt_entry || [];
                    let remarks = []
                    
                    // Iterate through each row in receipt_entry
                    receipt_entry.forEach(entry => {
                        if (remainingUnallocated > 0) {
                            // Calculate outstanding difference for this row
                            const outstanding = parseFloat(entry.outstanding_amount) || 0;
                            const alreadyAllocated = parseFloat(entry.allocated_amount) || 0;
                            const outstandingDifference = outstanding - alreadyAllocated;
                            
                            if (outstandingDifference > 0) {
                                // Determine amount to allocate to this row
                                const amountToAllocate = Math.min(remainingUnallocated, outstandingDifference);
                                
                                // Update custom_emp_liability_amount for this row
                                entry.custom_emp_liability_amount = 

                                    (parseFloat(entry.custom_emp_liability_amount) || 0) + amountToAllocate;

                                                      // Construct remark entry
                        let remarkEntry = `₹${amountToAllocate.toFixed(2)} allocated to ${frm.doc.executive} for ${entry.reference_type}: ${entry.reference_name}.`;
                        remarks.push(remarkEntry);    
                                
                                // Reduce remaining unallocated amount
                                remainingUnallocated -= amountToAllocate;
                            }
                        }
                    });
                    
                    // Update parent's unallocated_amount
                    frm.set_value('unallocated_amount', remainingUnallocated);
                    frm.refresh_field('receipt_entry');
                    
                    if (remarks.length > 0) {
                        frm.set_value('remark', remarks.join('\n')); // Join all remarks with a new line
                    } else {
                        frm.set_value('remark', 'No allocations made.');
                    }

                    frm.set_value('custom_is_employee_liability', 1);

        
                    frm.refresh_field('remark');
                    
                    if (remainingUnallocated === 0) {
                        frappe.validated = true;
                        d.hide();
                    } else {
                        frappe.msgprint(__(`Could only allocate ${frm.doc.unallocated_amount - remainingUnallocated}. Remaining unallocated amount: ${remainingUnallocated}`));
                        d.hide();
                    }
                },
                secondary_action() {
                    frappe.validated = false;
                    frappe.msgprint(__('Please allocate the unallocated amount before proceeding.'));
                    d.hide();
                }
            });
            
            d.show();
            return;
        }
        // Validate main document fields
        if (!frm.doc.amount || parseFloat(frm.doc.amount) <= 0) {
            frappe.msgprint(__('Amount is required and should be greater than zero.'));
            is_main_doc_valid = false;
        }
        if (frm.doc.unallocated_amount > 0 ) {
            frappe.msgprint(__('Unallocated Amount should be zero.'));
            is_main_doc_valid = false;
        }
        if (!frm.doc.mode_of_payment) {
            frappe.msgprint(__('Mode of payment is required.'));
            is_main_doc_valid = false;
        }
        if (!frm.doc.date) {
            frappe.msgprint(__('Date is required.'));
            is_main_doc_valid = false;
        }

        // If main document validation fails, prevent saving the form
        if (!is_main_doc_valid) {
            frappe.validated = false;
            return;
        }

        // Validate customer and entries tables
        // if (frm.doc.custom_deposited_by_customer && (!frm.doc.customer || frm.doc.customer.length === 0)) {
        //     frappe.msgprint(__('Please add at least one entry before proceeding'));
        //     return;
        // }
        if (!frm.doc.entries || frm.doc.entries.length === 0) {
            frappe.msgprint(__('Please add at least one outstanding entry before proceeding'));
            return;
        }

        // Validate each row in the customer table
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
        let total_amount = 0;
        frm.doc.entries.forEach(entry => {
            let entry_amount = parseFloat(entry.amount);
            if (entry_amount <= 0) {
                is_entry_valid = false;
                frappe.msgprint({
                    title: __('Validation Error'),
                    indicator: 'red',
                    message: __('Entry {0} has an amount of {1} for the given {2}, which is not greater than zero.', [entry.customer, entry.amount, entry.type])
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
                company: frm.doc.custom_company,
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

        console.log("Custom button clicked");

        // If all entries are valid, proceed with the frappe.call
        if (is_cust_valid && is_entry_valid) {
            frappe.call({
                method: 'sil.services.paymentDetails.paymentEntry', // Path to your method
                args: {
                    frm: frm.doc, // Pass the document data
                    formData: JSON.stringify(formData, null, 2)
                },
                callback: function (response) {
                    // Handle the response here
                    console.log(response.message);
                    if (response.message) {
                        frappe.msgprint({
                            title: __('Success'),
                            indicator: 'blue',
                            message: __('Payment saved Successfully')
                        });
                        // Handle successful response
                        console.log("Received from server:", response.message.message);
                    } else {
                        frappe.msgprint({
                            title: __('Validation Error'),
                            indicator: 'red',
                            message: __("No response from server or error occurred.")
                        });
                        // Handle error or empty response
                        console.log("No response from server or error occurred.");
                    }
                },
                error: function (error) {
                    // Handle the error
                    frappe.msgprint({
                        title: __('Validation Error'),
                        indicator: 'red',
                        message: __("No response from server or error occurred.")
                    });                    
                    
                    
                    console.error("An error occurred:", error);
                }
            });
        } else {
            // Prevent form from being saved if validation fails
            frappe.validated = false;
        }
    }
});