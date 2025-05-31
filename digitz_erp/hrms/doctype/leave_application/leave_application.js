// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Application", {
    refresh: function(frm) {
        // Refresh the form to show the field if already calculated
        if (frm.doc.no_of_leaves) {
            frm.toggle_display('no_of_leaves', true);
        }
    },
    setup: function(frm){
        frm.set_query('leave_type', function() {
            return {
                filters: {
                    "disabled": 0
                }
            };
        }); 
    },
    leave_from_date: function(frm) {
        frm.set_value('leave_to_date', frm.doc.leave_from_date);
        get_no_of_days_and_leave_period_without_holidays(frm);
        check_and_get_statistics(frm);
        get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm);
    },
    leave_to_date: function(frm) {
        get_no_of_days_and_leave_period_without_holidays(frm);
        check_and_get_statistics(frm);
        get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm);
    },    
    leave_duration:function(frm)
    {
        get_no_of_days_and_leave_period_without_holidays(frm);
        get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm);
    },
    employee: function(frm) {
        console.log(frm.doc.employee);
        console.log(frm.doc.leave_period);
        check_employee_leave_assignment(frm,frm.doc.employee)
        get_holiday_list(frm, frm.doc.employee, frm.doc.leave_period);
        check_and_get_statistics(frm);
    },
    leave_period: function(frm) {
        get_holiday_list(frm, frm.doc.employee, frm.doc.leave_period);
        check_and_get_statistics(frm);
        get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm);
    },
    holiday_list:function(frm)
    {
        get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm);
    },
    leave_type:function(frm)
    {
        get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm);
    }
});

function check_and_get_statistics(frm) {
    if (frm.doc.employee && frm.doc.leave_period && frm.doc.leave_from_date && frm.doc.leave_to_date) {
        console.log("before calling statistics");
        get_employee_leave_statistics(frm);
    }
}

function get_employee_leave_statistics(frm) {

    frm.clear_table('leave_balances');

    if (!(frm.doc.employee && frm.doc.leave_period && frm.doc.leave_from_date && frm.doc.leave_to_date)) {
        frappe.msgprint("Select the mandatory fields.");
    } else {
        frappe.call({
            method: 'digitz_erp.api.leave_application_api.get_employee_leave_statistics',
            args: {
                employee: frm.doc.employee,
                leave_period: frm.doc.leave_period,
                leave_from_date: frm.doc.leave_from_date,
                leave_to_date: frm.doc.leave_to_date
            },
            callback: function(r) {
                if (r.message) {
                    // Clear existing rows in the child table
                    frm.clear_table('leave_balances');

                    // Add new rows with the returned data
                    r.message.forEach(function(row) {
                        var child = frm.add_child('leave_balances');
                        frappe.model.set_value(child.doctype, child.name, 'leave_type', row.leave_type);
                        frappe.model.set_value(child.doctype, child.name, 'total_allocated', row.annual_allocation);
                        frappe.model.set_value(child.doctype, child.name, 'leaves_taken', row.leaves_taken);
                        var balance = row.annual_allocation - row.leaves_taken;
                        frappe.model.set_value(child.doctype, child.name, 'balance_leaves', balance);
                    });

                    // Refresh the field to show the updated child table
                    frm.refresh_field('leave_balances');
                }
            }
        });     
    }
}

function get_leave_period(frm) {
    
    console.log("fromn get_leave period")

    frappe.call({
        method: 'digitz_erp.api.leave_application_api.get_leave_period',
        args: {
            from_date: frm.doc.leave_from_date,
            to_date: frm.doc.leave_to_date
        },
        callback: function(r) {

            console.log("leave period")

            console.log(r)
            if (r.message) {
                frm.set_value("leave_period", r.message);
                frm.toggle_display("leave_period",true);
            }
        }
    });        
}

// Holidays are fetching only after selecting leave_type and 
//is doing with the method get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records
function get_no_of_days_and_leave_period_without_holidays(frm) {
    if (frm.doc.leave_from_date && frm.doc.leave_to_date) {
        let from_date = new Date(frm.doc.leave_from_date);
        let to_date = new Date(frm.doc.leave_to_date);

        if (from_date > to_date) {
            frappe.msgprint("From Date cannot be greater than To Date");
            frm.set_value('no_of_leaves', 0);
            frm.toggle_display('no_of_leaves', true);
            return;
        }

        let time_difference = to_date - from_date;
        let days_difference = Math.round(time_difference / (1000 * 3600 * 24)) + 1; // Adding 1 to include the start date

        if(frm.doc.leave_duration == "Half Day Morning" || frm.doc.leave_duration == "Half Day Afternoon")
        {
            days_difference = days_difference * .5
        }

        frm.set_value('no_of_leaves', days_difference);        
        frm.toggle_display('no_of_leaves', true);

        get_leave_period(frm);
    }
}

function get_holiday_list(frm, employee, leave_period) {
    if (employee && leave_period) {
        frappe.call({
            method: 'digitz_erp.api.leave_application_api.get_employee_holiday_list',
            args: {
                employee: employee,
                leave_period: leave_period
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value("holiday_list", r.message);
                    frm.toggle_display("holiday_list", true);
                }
            }
        }); 
    }
}

function get_leaves_and_holidays_count_for_leave_type_and_assign_leave_records(frm)
{
    if(frm.doc.leave_from_date && frm.doc.leave_to_date && frm.doc.holiday_list && frm.doc.leave_type )
    {
        frappe.call({
            method: 'digitz_erp.api.leave_application_api.get_leave_and_holiday_count',            
            args: {
                leave_type:frm.doc.leave_type,
                holiday_list:frm.doc.holiday_list,
                from_date: frm.doc.leave_from_date,
                to_date: frm.doc.leave_to_date
            },
            callback: function(r) {
                if (r.message) {

                    if(frm.doc.leave_duration == "Half Day Morning" || frm.doc.leave_duration=="Half Day Afternoon")
                    {
                        frm.set_value("no_of_leaves", r.message.leave_count/2);
                    }
                    else
                    {
                        frm.set_value("no_of_leaves", r.message.leave_count);
                    }

                    frm.set_value("no_of_holidays_during_leave_period", r.message.holiday_count);
                } 
            }
        }); 

        set_leave_records(frm);

    }
}

function set_leave_records(frm) {
    let leave_type = frm.doc.leave_type;
    let holiday_list = frm.doc.holiday_list;
    let from_date = frm.doc.leave_from_date;
    let to_date = frm.doc.leave_to_date;

    // if (!leave_type || !holiday_list || !from_date || !to_date) {
    //     frappe.msgprint(__('Please fill in all required fields.'));
    //     return;
    // }

    frappe.call({
        method: 'digitz_erp.api.leave_application_api.get_leave_dates_excluding_holidays',
        args: {
            leave_type: leave_type,
            holiday_list: holiday_list,
            from_date: from_date,
            to_date: to_date
        },
        callback: function(r) {
            if (r.message) {

                console.log(r.message)

                let is_leave_without_pay = false;                
                let is_partially_paid_leave = false
                let is_compensatory_leave = false
                let count_holidays_in_leaves_as_leaves=false

                frappe.call({
                    method: 'digitz_erp.api.leave_application_api.get_leave_type_details',
                    args: {
                        leave_type: leave_type
                    },
                    callback: function(r) {
                        if (r.message) {
                            is_leave_without_pay = r.message.is_leave_without_pay;
                            is_partially_paid_leave = r.message.is_partially_paid_leave
                            is_compensatory_leave = r.message.is_compensatory_leave
                            count_holidays_in_leaves_as_leaves = r.message.count_holidays_in_leaves_as_leaves
                        }
                    }});

                let leave_dates = r.message;

                console.log("leave_dates")
                console.log(leave_dates)

                // Clear existing child table rows
                frm.clear_table('leave_records');

                // Add fetched leave dates to child table
                leave_dates.forEach(date => {

                    console.log(date)
                    
                    let child = frm.add_child('leave_records');
                    frappe.model.set_value(child.doctype, child.name, 'leave_date', date);
                    frappe.model.set_value(child.doctype, child.name, 'leave_type', frm.doc.leave_type);
                    frappe.model.set_value(child.doctype, child.name, 'is_leave_without_pay', is_leave_without_pay);
                    frappe.model.set_value(child.doctype, child.name, 'is_partially_paid_leave', is_partially_paid_leave);
                    frappe.model.set_value(child.doctype, child.name, 'is_compensatory_leave', is_compensatory_leave);

                    // If you have other fields to fill, set them here
                });

                // Refresh the form to show the updated child table
                frm.refresh_field('leave_records');
            }
        }
    });    
}

// Method to just verify if any leave assignment exist for the employee and if not throw a message
function check_employee_leave_assignment(frm, employee) {
    if (employee) {
        frappe.call({
            method: 'digitz_erp.api.leave_application_api.check_employee_leave_assignment',
            args: {
                employee: employee                    
            },
            callback: function(r) {

                console.log(r)

                if (r.message == false)
                {
                    frappe.throw("No leave policy has been assigned to the selected employee.")
                }
                
            }
        }); 
    }
}