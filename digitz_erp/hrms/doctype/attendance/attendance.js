frappe.ui.form.on("Attendance", {
    onload(frm) {

        if(frm.is_new())
        {            
            assign_defaults(frm);
        }
        else{
            let attendance_date = frm.doc.attendance_date;
            get_employee_attendance_calendar(frm, attendance_date)
        }
    },
    setup: function (frm) {
        
        frm.add_fetch('shift', 'end_time', 'attendance_end_time')
    },
    employee:function(frm) {		
        get_employee_shift_default_values(frm);    
        let attendance_date = frm.doc.attendance_date;
        console.log("executed")
        get_employee_attendance_calendar(frm, attendance_date)    
    },
    
    attendance_status:function(frm)
    {
        if(frm.doc.attendance_status == "Absent" || frm.doc.attendance_status == "On Leave" || frm.doc.attendance_status == "Half Day Morning" || frm.doc.attendance_status == "Half Day Afternoon")
        {
            frm.doc.attendance_start_time = null
            frm.doc.attendance_end_time = null
            frm.refresh_field('attendance_start_time')
            frm.refresh_field('attendance_end_time')
            frm.set_value('attendance_ot',0)
            frm.set_value('worked_hours',0)
        }

        if(frm.doc.attendance_status == "Present" || frm.doc.attendance_status == "Work From Home")
        {
            frm.set_value("attendance_start_time", frm.doc.shift_start_time)
            frm.set_value("attendance_end_time", frm.doc.shift_end_time)
        }
    },
    attendance_date:function(frm)
    {
        get_employee_shift_default_values(frm);
        let attendance_date = frm.doc.attendance_date;
        get_employee_attendance_calendar(frm, attendance_date)        
    }
});

function get_employee_shift_default_values(frm) {
    // Somehow after_save start_time, end_time getting resets. Checks is_new to avoid it.
    
    let employee = frm.doc.employee;

    if (employee) {

        let validate = true;

        frappe.call({
            method: 'digitz_erp.api.employee_api.validate_employee_shift',
            args: {
                employee: employee,
                shift_date: frm.doc.attendance_date
            },
            callback: (r) => {    
                console.log("execution checking",r) 
                if (r.message === false) {
                    frappe.throw("Shift not allocated for the employee. Shift Allocation mandatory as per HR Settings.");
                    validate = false;
                } else {
                    // Proceed only if validation passes
                    frappe.call({
                        method: 'digitz_erp.api.employee_api.get_employee_shift',
                        args: {
                            employee: employee,
                            shift_date: frm.doc.attendance_date
                        },
                        callback: (r) => {     
                            let shift = r.message[0];
                            let shift_allocation = r.message[1];
    
                            frm.set_value('shift', shift.name);
                            frm.set_value('attendance_start_time', shift.start_time);
                            frm.set_value('attendance_end_time', shift.end_time);
                            frm.set_value('actual_no_of_units', shift.no_of_units_per_day);
    
                            if (shift_allocation != null) {
                                frm.set_value('attendance_end_time', shift_allocation.expected_end_time);
                                frm.set_value('actual_no_of_units', shift_allocation.expected_no_of_units); 
                                frm.set_value('effective_no_of_units', shift_allocation.expected_no_of_units);                                       
                                frm.set_value('attendance_ot', shift_allocation.expected_ot);
                            }
                        }
                    });
                }
            }            
        });
    }
}


function assign_defaults(frm) {
    if (frm.is_new()) {
        
    }
}

function get_employee_attendance_calendar(frm, attendance_date) {
    let employee = frm.doc.employee;

    if (employee && attendance_date) {
        frappe.call({
            method: 'digitz_erp.api.employee_api.get_employee_monthly_attendance_for_calendar',
            args: {
                employee_code: employee,
                reference_date: attendance_date
            },
            callback: function(r) {
                console.log(r.message);

                if (r.message) {
                    let attendance_statuses = r.message;
                    let html_content = generate_calendar(attendance_statuses, frm.doc.employee_name, attendance_date, frm);
                    // Update the HTML field
                    frm.fields_dict.attendance_calendar.html(html_content);
                }
            }
        });
    } else {
        frappe.msgprint('Please select an employee and start date.');
    }
}

function generate_calendar(attendance_statuses, employee_name, attendance_date, frm) {
    // Ensure attendance_statuses is not empty
    if (Object.keys(attendance_statuses).length === 0) {
        return '<div style="text-align: center; margin-bottom: 20px;">No attendance data available.</div>';
    }

    // Get the year and month from the provided date
    let currentDate = new Date(attendance_date);
    let year = currentDate.getFullYear();
    let month = currentDate.getMonth();
    let monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    // Create a new date object for the first day of the month
    let firstDay = new Date(year, month, 1);
    let lastDay = new Date(year, month + 1, 0);

    // Create a table for the calendar
    let calendar = `
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <button id="prev-month" style="font-size: 1.2em;">&#9664;</button>
                <h3 style="margin: 0; padding: 10px; border-bottom: 2px solid #ccc;">
                    Attendance Calendar for ${employee_name} - ${monthNames[month]} ${year}
                </h3>
                <button id="next-month" style="font-size: 1.2em;">&#9654;</button>
            </div>
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

        calendar += `<td style="text-align: center; padding: 10px; background-color: ${statusColor};">
                        <div style="font-size: 1.2em;">${day}</div>
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
        <div style="text-align: left; margin-top: 20px; font-size: 0.9em;">
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: green; color: white;">P - Present</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: orange; color: white;">L - Leave</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: yellow; color: black;">HM - Half Day Morning</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: yellow; color: black;">HA - Half Day Afternoon</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: red; color: white;">A - Absent</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: lightblue; color: black;">Holiday</div>
            <div style="display: inline-block; margin: 0 10px; padding: 5px; background-color: grey; color: white;">NE - Not Entered</div>
        </div>`;

    // Add event listeners to navigation buttons
    setTimeout(() => {
        document.getElementById('prev-month').addEventListener('click', () => {
            let newDate = new Date(year, month - 1);
            let newAttendanceDate = `${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, '0')}-01`;
            get_employee_attendance_calendar(frm, newAttendanceDate);
        });
        document.getElementById('next-month').addEventListener('click', () => {
            let newDate = new Date(year, month + 1);
            let newAttendanceDate = `${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, '0')}-01`;
            get_employee_attendance_calendar(frm, newAttendanceDate);
        });
    }, 100);

    return calendar + legend;
}
