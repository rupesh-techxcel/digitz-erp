// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {
        frm.toggle_display('create_salary_slips', !frm.is_new());
    },
    onload(frm) {
        if (frm.is_new()) {
            assign_defaults(frm);
        }
    },
    start_date(frm) {
        if (frm.doc.start_date) {
            const start_date = new Date(frm.doc.start_date);
            const next_month_first_date = new Date(start_date.getFullYear(), start_date.getMonth() + 1, 1);
            const end_date = new Date(next_month_first_date - 1);
            frm.set_value('end_date', end_date.toISOString().split('T')[0]);
        }

        get_data(frm);
    },
    end_date(frm) {
        get_data(frm);
    },
    get_employees(frm) {
        get_employees_for_payroll(frm);
    },
    create_salary_slips(frm) {
        let from_date = frm.doc.start_date;
        let to_date = frm.doc.end_date;
    
        let valid_count = 0;
    
        if (from_date && to_date) {
            frm.doc.payroll_entry_details.forEach(function (payroll_entry) {
                if (payroll_entry.data_status === "Completed") {
                    console.log("payroll_entry.employee");
                    console.log(payroll_entry.employee);
    
                    frappe.call({
                        method: 'digitz_erp.api.employee_api.create_salary_slip',
                        args: {
                            employee: payroll_entry.employee,
                            payroll_date: frm.doc.posting_date,
                            start_date: frm.doc.start_date,
                            end_date: frm.doc.end_date
                        },
                        async:false,
                        callback: (r) => {
                            
                            
                        }
                    });
                }
            });
            
            frm.reload_doc();
        }
    },
    
    verify(frm) {
        show_employees_calendar(frm);
    },
    show_review(frm)
    {
        get_data(frm)
    }
});

frappe.ui.form.on("Payroll Entry Detail", {
    show_data: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let employee = row.employee;
        let employee_name = row.employee_name; // Add employee_name parameter
        let start_date = frm.doc.start_date;
        let end_date = frm.doc.end_date;

        get_employee_attendance_calendar(employee, employee_name, start_date, end_date, frm);
    }
});

function get_employee_attendance_calendar(employee, employee_name, start_date, end_date, frm) {
    if (employee && start_date && end_date) {
        frappe.call({
            method: 'digitz_erp.api.employee_api.get_employee_monthly_attendance_for_calendar',
            args: {
                employee_code: employee,
                start_date: start_date,
                last_date: end_date
            },
            callback: function(r) {
                if (r.message) {
                    let attendance_statuses = r.message;
                    let html_content = generate_calendar_for_employee(attendance_statuses, employee_name, start_date, end_date);

                    // Create and show the dialog with the calendar
                    let d = new frappe.ui.Dialog({
                        title: __('Attendance Calendar'),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'calendar_html'
                            }
                        ],
                        size: 'large' // Make the dialog larger
                    });

                    d.$wrapper.find('.modal-dialog').css("width", "90%"); // Adjust the width of the dialog
                    d.$wrapper.find('.modal-content').css("height", "80%"); // Adjust the height of the content

                    d.fields_dict.calendar_html.$wrapper.html(html_content);
                    d.show();
                }
            }
        });
    } else {
        frappe.msgprint('Please select an employee and specify the start and end dates.');
    }
}

function generate_calendar_for_employee(attendance_statuses, employee_name, start_date, end_date) {
    // Ensure attendance_statuses is not empty
    if (Object.keys(attendance_statuses).length === 0) {
        return '<div style="text-align: center; margin-bottom: 20px;">No attendance data available.</div>';
    }

    // Get the year and month from the provided start_date
    let startDate = new Date(start_date);
    let endDate = new Date(end_date);
    let year = startDate.getFullYear();
    let month = startDate.getMonth();
    let monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    // Create a new date object for the first day of the month
    let firstDay = new Date(year, month, 1);
    let lastDay = new Date(year, month + 1, 0);

    // Create a table for the calendar
    let calendar = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin: 0; padding: 10px; border-bottom: 2px solid #ccc;">
                Attendance Calendar for ${employee_name} - ${monthNames[month]} ${year}
            </h3>
        </div>
        <table class='table table-bordered' style='margin: 0 auto; width: 100%; font-size: 1.2em; border: 2px solid #ccc;'>
            <thead>
                <tr>
                    <th style="text-align: center; padding: 8px;">Sun</th>
                    <th style="text-align: center; padding: 8px;">Mon</th>
                    <th style="text-align: center; padding: 8px;">Tue</th>
                    <th style="text-align: center; padding: 8px;">Wed</th>
                    <th style="text-align: center; padding: 8px;">Thu</th>
                    <th style="text-align: center; padding: 8px;">Fri</th>
                    <th style="text-align: center; padding: 8px;">Sat</th>
                </tr>
            </thead>
            <tbody>
                <tr>`;

    // Fill the first row with empty cells until the first day of the month
    for (let i = 0; i < firstDay.getDay(); i++) {
        calendar += "<td></td>";
    }

    // Fill the days of the month
    for (let day = 1; day <= lastDay.getDate(); day++) {
        let currentDate = new Date(year, month, day);
        let formattedDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        let attendanceStatus = attendance_statuses[formattedDate] || '';

        let statusColor = '';
        if (attendanceStatus === 'P') {
            statusColor = 'green';
        } else if (attendanceStatus === 'L') {
            statusColor = 'orange';
        } else if (attendanceStatus === 'HM' || attendanceStatus === 'HA') {
            statusColor = 'yellow';
        } else if (attendanceStatus === 'A') {
            statusColor = 'red';
        } else if (attendanceStatus === 'Holiday') {
            statusColor = 'lightblue';
        } else if (attendanceStatus === 'NE') {
            statusColor = 'grey';
        }

        calendar += `<td style="text-align: center; padding: 8px; background-color: ${statusColor};">
                        <div style="font-size: 1em;">${day}</div>
                        <div style="font-size: 0.8em;">${attendanceStatus}</div>
                    </td>`;

        // If the current day is Saturday, close the row and start a new one
        if (currentDate.getDay() === 6 && day !== lastDay.getDate()) {
            calendar += "</tr><tr>";
        }
    }

    // Fill the last row with empty cells if needed
    for (let i = lastDay.getDay() + 1; i <= 6; i++) {
        calendar += "<td></td>";
    }

    calendar += "</tr></tbody></table>";

    // Define legend items
    let legend = `
        <div style="text-align: left; margin-top: 20px; font-size: 0.8em;">
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: green; color: white;">P - Present</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: orange; color: white;">L - Leave</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: yellow; color: black;">HM - Half Day Morning</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: yellow; color: black;">HA - Half Day Afternoon</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: red; color: white;">A - Absent</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: lightblue; color: black;">Holiday</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: grey; color: white;">NE - Not Entered</div>
        </div>`;

    return calendar + legend;
}


function assign_defaults(frm) {
    frm.set_value('start_date', frappe.datetime.month_start());
    frm.set_value('end_date', frappe.datetime.month_end());
    get_data(frm);
}

function show_employees_calendar(frm) {
    console.log("call method verify_attendance");
    let from_date = frm.doc.start_date;
    let to_date = frm.doc.end_date;

    if (from_date && to_date) {
        frappe.call({
            method: 'digitz_erp.api.employee_api.verify_attendances',
            args: {
                from_date: from_date,
                to_date: to_date
            },
            callback: function (r) {
                console.log(r.message);
                if (r.message) {
                    let exception_counts = r.message;
                    let html_content = generate_calendar(exception_counts);
                    frm.fields_dict.missing_attendances.html(html_content);
                }
            }
        });
    }
}

function generate_calendar(exception_counts) {
    let firstDate = new Date(Object.keys(exception_counts)[0]);
    let year = firstDate.getFullYear();
    let month = firstDate.getMonth();
    let monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    let firstDay = new Date(year, month, 1);
    let lastDay = new Date(year, month + 1, 0);

    let calendar = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin: 0; padding: 10px; border-bottom: 2px solid #ccc;">Missing Attendances</h3>
            <h4 style="margin: 10px 0; padding: 10px; color: blue;">${monthNames[month]} ${year}</h4>
        </div>
        <table class='table table-bordered' style='margin: 0 auto; width: 100%; font-size: 1.5em; border: 2px solid #ccc;'>
            <thead>
                <tr>
                    <th style="text-align: center; padding: 10px;">Sun</th>
                    <th style="text-align: center; padding: 10px;">Mon</th>
                    <th style="text-align: center; padding: 10px;">Tue</th>
                    <th style="text-align: center; padding: 10px;">Wed</th>
                    <th style="text-align: center; padding: 10px;">Thu</th>
                    <th style="text-align: center; padding: 10px;">Fri</th>
                    <th style="text-align: center; padding: 10px;">Sat</th>
                </tr>
            </thead>
            <tbody>
                <tr>`;

    for (let i = 0; i < firstDay.getDay(); i++) {
        calendar += "<td></td>";
    }

    for (let day = 1; day <= lastDay.getDate(); day++) {
        let currentDate = new Date(year, month, day);
        let formattedDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        let exceptionCount = exception_counts[formattedDate] ? `<div style="font-size: 0.75em; color: red;">${exception_counts[formattedDate]}</div>` : '';

        if (exception_counts[formattedDate]) {
            calendar += `<td style="background-color: #f8d7da; text-align: center; padding: 10px;">${exceptionCount}${day}</td>`;
        } else {
            calendar += `<td style="text-align: center; padding: 10px;">${day}</td>`;
        }

        if (currentDate.getDay() === 6 && day !== lastDay.getDate()) {
            calendar += "</tr><tr>";
        }
    }

    for (let i = lastDay.getDay() + 1; i <= 6; i++) {
        calendar += "<td></td>";
    }

    calendar += "</tr></tbody></table>";
    return calendar;
}

function get_employees_for_payroll(frm) {
    frappe.call({
        method: 'digitz_erp.api.employee_api.get_employees_for_payroll',
        args: {
            start_date: frm.doc.start_date,
            end_date: frm.doc.end_date
        },
        callback: (r) => {
            // Clear the existing table data
            frm.clear_table('payroll_entry_details');
            
            // Iterate through each employee returned by the API
            r.message.forEach(employee => {
                // Add a new child row in the 'payroll_entry_details' table
                let child = frm.add_child('payroll_entry_details');
                
                // Set the child row fields with employee data
                child.employee = employee.employee;
                child.employee_name = employee.employee_name;
                child.designation = employee.designation;
                child.department = employee.department;

                // Check the employee data status
                let data_status = get_employee_data_status(frm, employee.employee);
                
                // Log the data status for debugging purposes
                console.log(data_status);

                // Set the 'data_status' field based on the data status
                child.data_status = data_status ? "Completed" : "Pending";
            });

            // Refresh the field to update the table in the UI
            frm.refresh_field('payroll_entry_details');
        }
    });
}

function fetch_employee_data(frm) {
    let start_date = frm.doc.start_date;
    let end_date = frm.doc.end_date;

    console.log("fetch employee data")

    if (!start_date || !end_date) {
        frappe.msgprint(__('Please select both Start Date and End Date'));
        return;
    }

    frappe.call({
        method: 'digitz_erp.api.employee_api.get_all_employees_monthly_attendance',
        args: {
            start_date: start_date,
            end_date: end_date
        },
        callback: function (r) {
            if (r.message) {

                console.log("r.message")
                console.log(r.message)

                frm.clear_table('employees_data');
                $.each(r.message, function (employee_code, data) {
                    let child = frm.add_child('employees_data');
                    child.employee = employee_code;
                    child.employee_name = data['Employee Name'];
                    child.attendance_count = data['Present Count'];
                    child.leave_count = data['Leave Count'];
                    child.not_entered = data['Not Entered Count'];
                    child.absent_count = data['Absent Count'];
                });
                frm.refresh_field('employees_data');
            }
        }
    });
}

// For Details tab with employee list
// For Details tab with employee list
function get_employee_data_status(frm, employee) {
    
    let start_date = frm.doc.start_date;
    let end_date = frm.doc.end_date;
    let invalid_data_found = false;

    frappe.call({
        method: 'digitz_erp.api.employee_api.get_employee_monthly_attendance_status',
        args: {
            employee: employee,
            start_date: start_date,
            end_date: end_date
        },
        async: false,
        callback: function (r) {
            if (r.message) {
                console.log(r.message);
                invalid_data_found = r.message;
            }
        }
    });

    console.log("invalid_data_found")
    console.log(invalid_data_found)
    return !invalid_data_found;
}


function get_data(frm) {
    get_employees_for_payroll(frm);
    show_employees_calendar(frm);
    fetch_employee_data(frm);
}
