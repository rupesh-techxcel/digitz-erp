// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Loan", {

	refresh(frm) {

	},
    setup(frm)
    {
        frm.set_query("employee", function () {
			return {
				"filters": {
					"status": "On Job"                    
				}
			};
		});
    },
    employee(frm)
    {
        frm.events.get_loan_history(frm);
    },
    date(frm)
    {
        frm.events.set_recovery_start_date(frm)
        frm.events.get_loan_history(frm);
    },
    loan_amount(frm)
    {
        frm.events.get_installments(frm)
    },
    monthly_deduction_amount(frm)
    {
        frm.events.get_installments(frm)
    },
    recovery_start_date(frm)
    {
        frm.events.get_installments(frm)
    },
    get_installments(frm)
    {
        if (frm.doc.loan_amount && frm.doc.loan_amount >0 && frm.doc.monthly_deduction_amount && frm.doc.monthly_deduction_amount>0)        
            {
                installment_amount =frm.doc.loan_amount / frm.doc.monthly_deduction_amount
                frm.set_value('no_of_instalment_for_recovery', installment_amount)
                frm.events.calculate_installments(frm)
            }
    },
    set_recovery_start_date: function(frm) {
        if (frm.doc.date && !frm.doc.recovery_start_date) {
            // Add one month to the current date
            const next_month_date = frappe.datetime.add_months(frm.doc.date, 1);
    
            frm.set_value('recovery_start_date', next_month_date);
        }
    },               
    get_loan_history: function(frm) {
        if (frm.doc.employee && frm.doc.date) {
            frappe.call({
                method:'digitz_hr.digitz_hrms.doctype.employee_loan.employee_loan.get_employee_loan_history',                
                args: {
                    employee: frm.doc.employee,
                    date: frm.doc.date
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        frm.events.render_loan_history(frm, r.message);
                    } else {
                        frm.get_field('loan_history_html').$wrapper.html('<p>No loan history available for the selected employee and date.</p>');
                    }
                }
            });
        }
    },

    render_loan_history: function(frm, loan_history) {
        const wrapper = frm.get_field('loan_history_html').$wrapper.empty();

        const table = $('<table class="table table-bordered">')
            .append('<tr><th>Loan Doc</th><th>Loan Date</th><th>Loan Amount</th><th>Loan Status</th><th>Total Deducted Amount</th><th>Balance to be Deducted</th></tr>');

        loan_history.forEach(function(entry) {
            const loan_date = new Date(entry.loan_date);
            const formatted_date = ('0' + loan_date.getDate()).slice(-2) + '-' + 
                                   ('0' + (loan_date.getMonth() + 1)).slice(-2) + '-' + 
                                   loan_date.getFullYear();

            const formatted_loan_amount = format_currency(entry.loan_amount);
            const formatted_total_deducted_amount = format_currency(entry.total_deducted_amount);
            const formatted_balance_to_be_deducted = format_currency(entry.balance_to_be_deducted);

            const row = $('<tr>').append(
                $('<td>').html(`<a href="/app/employee-loan/${entry.name}" target="_blank">${entry.name}</a>`),
                $('<td>').text(formatted_date),
                $('<td>').text(formatted_loan_amount),
                $('<td>').text(entry.loan_status),
                $('<td>').text(formatted_total_deducted_amount),
                $('<td>').text(formatted_balance_to_be_deducted)
            );
            table.append(row);
        });

        wrapper.append(table);
    },
    calculate_installments: function(frm) {
        if (frm.doc.loan_amount && frm.doc.monthly_deduction_amount && frm.doc.no_of_instalment_for_recovery && frm.doc.recovery_start_date) {

            const loan_amount = parseFloat(frm.doc.loan_amount);
            const monthly_deduction = parseFloat(frm.doc.monthly_deduction_amount);
         


            let no_of_installments = parseInt(frm.doc.no_of_instalment_for_recovery);

            if(frm.doc.no_of_instalment_for_recovery> parseInt(frm.doc.no_of_instalment_for_recovery))
            {
                no_of_installments++;
            }

            const recovery_start_date = new Date(frm.doc.recovery_start_date);

            let installments = [];
            let balance = loan_amount;
            let current_date = new Date(recovery_start_date);

            for (let i = 0; i < no_of_installments; i++) {
                let installment_amount = monthly_deduction;
                if (i === no_of_installments - 1 || balance < monthly_deduction) {
                    installment_amount = balance; // Last installment or if balance is less than monthly deduction
                }

                installments.push({
                    installment_date: current_date.toISOString().split('T')[0],
                    installment_amount: installment_amount.toFixed(2),
                    balance: (balance - installment_amount).toFixed(2)
                });

                balance -= installment_amount;
                current_date.setMonth(current_date.getMonth() + 1);
            }

            frm.clear_table('deduction_records');
            installments.forEach(installment => {
                let child = frm.add_child('deduction_records');
                child.date = installment.installment_date;
                child.deduction_amount = installment.installment_amount;
                child.status = "Pending";
            });

            console.log("installments")
            console.log(installments)

            frm.refresh_field('deduction_records');

        } else {
            frappe.msgprint(__('Please fill in all the required fields to calculate installments.'));
        }
    }
});

function format_currency(value) {
    return new Intl.NumberFormat('ar-AE', { style: 'currency', currency: 'AED' }).format(value);
}