// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Head', {
    refresh: function (frm) {
        // Ensure the filters are applied when the form is refreshed
        apply_expense_account_filter(frm);
    },
    tax_excluded: function (frm) {
        if (frm.doc.tax_excluded == 1) {
            frm.set_value('tax_rate', 0);
        }
    },
    onload: function (frm) {
        // Set the filters when the form is loaded
        apply_expense_account_filter(frm);
    },
    expense_type: function (frm) {
        console.log("expense type changed")
        // Update the filters dynamically based on the expense_type field
        apply_expense_account_filter(frm);
    }
});

// Helper function to apply filters
function apply_expense_account_filter(frm) {
    console.log("Expense Type:", frm.doc.expense_type); // Log the expense_type value for debugging

    if (frm.doc.expense_type === 'Expense') {
        console.log("Applying filter for 'Expense'");
        frm.set_query('expense_account', function () {
            return {
                filters: {
                    is_group: 0, // 'is_group' is false
                    root_type: 'Expense' // root_type is 'Expense'
                }
            };
        });
    } else if (frm.doc.expense_type === 'Work In Progress') {
        console.log("Applying filter for 'Work In Progress'");
        frm.set_query('expense_account', function () {
            return {
                filters: {
                    account_type: 'Work In Progress', // account_type is 'Work In Progress'
                    is_group: 0 // Ensure it's not a group account
                }
            };
        });
    } else {
        console.log("Clearing filter for expense_account");
        frm.set_query('expense_account', function () {
            return {}; // Clear filters for other cases
        });
    }
}
