frappe.ui.form.on("Employee Attendance Tool", {
    refresh(frm) {
        frm.trigger("reset_attendance_fields");
        frm.trigger("load_employees");
        frm.trigger("set_primary_action");
        frm.add_custom_button(('Attendance List'), function() {
            // When button is clicked, redirect to the Attendance list
            frappe.set_route('List', 'Attendance');
        });        

        frm.add_custom_button(__('Create Full Attendance for the month'), function() {
            // Call your method when the button is clicked
            
            frm.trigger("mark_attendance_for_whole_month");
        });
    },

    onload(frm) {
        frm.set_value("date", frappe.datetime.get_today());
    },

    date(frm) {
        frm.trigger("load_employees");
    },

    department(frm) {
        frm.trigger("load_employees");
    },
    designation(frm){
        frm.trigger("load_employees");
    },
    status(frm) {
        frm.trigger("set_primary_action");
    },

    reset_attendance_fields(frm) {
        frm.set_value("status", "")        
    },
    load_employees(frm) {
        if (!frm.doc.date)
            return;

        console.log("frm.doc.date")
        console.log(frm.doc.date)

        frappe.call({
            method: "digitz_hr.digitz_hrms.doctype.employee_attendance_tool.employee_attendance_tool.get_employees",
            args: {
                date: frm.doc.date,
                department: frm.doc.department,
                designation:frm.doc.designation
            }
        }).then((r) => {

            frm.employees = r.message["unmarked"];
            console.log("unmarked")
            console.log(frm.employees)

            if (r.message["unmarked"].length > 0) {
                frm.toggle_display("unmarked_attendance_section",true)
                frm.toggle_display("attendance_details_section",true)
                // unhide_field("unmarked_attendance_section");
                // unhide_field("attendance_details_section");
                frm.events.show_unmarked_employees(frm, r.message["unmarked"]);
            } else {
                console.log("else case")
                // frm.toggle_display("unmarked_attendance_section",false)
                // frm.toggle_display("attendance_details_section",false)         
                frm.events.show_unmarked_employees(frm, r.message["unmarked"]);       
            }

            if (r.message["marked"].length > 0) {
                unhide_field("marked_attendance_html");
                frm.events.show_marked_employees(frm, r.message["marked"]);
            } else {
                hide_field("marked_attendance_html");
            }
        });
    },

    show_unmarked_employees(frm, unmarked_employees) {
        const $wrapper = frm.get_field("employees_html").$wrapper;

        // Empty the content if unmarked_employees length is zero
        if (unmarked_employees.length === 0) {
            $wrapper.empty();
        
            $wrapper.append('<div>Invalid date for attendance.</div>');        
            return;
        }

        $wrapper.empty();
        const employee_wrapper = $(`<div class="employee_wrapper">`).appendTo($wrapper);

        frm.employees_multicheck = frappe.ui.form.make_control({
            parent: employee_wrapper,
            df: {
                fieldname: "employees_multicheck",
                fieldtype: "MultiCheck",
                select_all: true,
                columns: 4,
                get_data: () => {
                    return unmarked_employees.map((employee) => {
                        return {
                            label: `${employee.employee_code} : ${employee.employee_name}`,
                            value: employee.employee_code,
                            checked: 0,
                        };
                    });
                },
            },
            render_input: true,
        });

        frm.employees_multicheck.refresh_input();
    },
    show_marked_employees(frm, marked_employees) {
        const $wrapper = frm.get_field("marked_attendance_html").$wrapper;
        const summary_wrapper = $(`<div class="summary_wrapper">`).appendTo($wrapper);
    
        const data = marked_employees.map((entry) => {
            const employee_link = `<a href="/app/employee/${entry.employee}" target="_blank" style="color: blue;">${entry.employee}</a>`;
            const name_link = `<a href="/app/attendance/${entry.name}" target="_blank" style="color: blue;">${entry.name}</a>`;
    
            let status_color = '';
            switch (entry.attendance_status) {
                case 'Present':
                    status_color = 'green';
                    break;
                case 'Leave':
                    status_color = 'red';
                    break;
                case 'Half Day Morning':
                case 'Half Day Afternoon':
                    status_color = 'orange';
                    break;
            }
    
            const status_html = `<span style="color: ${status_color};">${entry.attendance_status}</span>`;
    
            let document_status = '';
            switch (entry.docstatus) {
                case 1:
                    document_status = "Submitted";
                    break;
                case 0:
                    document_status = "Draft";
                    break;
            }
    
            return [employee_link, entry.employee_name, status_html, name_link, document_status];
        });
    
        console.log(summary_wrapper)

        frm.events.render_datatable(frm, data, summary_wrapper);
    },
    
    render_datatable(frm, data, summary_wrapper) {
        const columns = frm.events.get_columns_for_marked_attendance_table(frm);
    
        if (!frm.marked_emp_datatable) {
            const datatable_options = {
                columns: columns,
                data: data,
                dynamicRowHeight: true,
                inlineFilters: true,
                layout: "fixed",
                cellHeight: 35,
                noDataMessage: __("No Data"),
                disableReorderColumn: true,
            };
            frm.marked_emp_datatable = new frappe.DataTable(
                summary_wrapper.get(0),
                datatable_options,
            );
        } else {
            frm.marked_emp_datatable.refresh(data, columns);
        }
    },    
    get_columns_for_marked_attendance_table(frm) {
        return [
            { id: 'employee', name: __('Employee'), width: 150, editable: false },
            { id: 'employee_name', name: __('Employee Name'), width: 250, editable: false },
            { id: 'attendance_status', name: __('Attendance Status'), width: 150, editable: false },
            { id: 'name', name: __('Attendance'), width: 150, editable: false },
            { id: 'docstatus', name: __('Doc Status'), width: 150, editable: false }

        ];
    }    
    ,
    set_primary_action(frm) {
        frm.disable_save();
        frm.page.set_primary_action(__("Mark Attendance"), () => {
            if (frm.employees.length === 0) {
                frappe.msgprint({
                    message: __("Attendance for all the employees under this criteria has been marked already."),
                    title: __("Attendance Marked"),
                    indicator: "green"
                });
                return;
            }

            if (frm.employees_multicheck.get_checked_options().length === 0) {
                frappe.throw({
                    message: __("Please select the employees you want to mark attendance for."),
                    title: __("Mandatory")
                });
            }

            if (!frm.doc.status) {
                frappe.throw({
                    message: __("Please select the attendance status."),
                    title: __("Mandatory")
                });
            }

            frm.trigger("mark_attendance");
        });
    },

    mark_attendance(frm) {

        const marked_employees = frm.employees_multicheck.get_checked_options();

        frappe.call({
            method: "digitz_hr.digitz_hrms.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance",
            args: {
                employee_list: marked_employees,
                employee_code: frm.doc.employee_code,
                status: frm.doc.status,
                date: frm.doc.date,
                late_entry: frm.doc.late_entry,
                early_exit: frm.doc.early_exit,
            },
            freeze: true,
            freeze_message: __("Marking Attendance")
        }).then((r) => {
            if (!r.exc) {
                
                frm.refresh();
            }
        });
    },
    mark_attendance_for_whole_month(frm) {


        if (frm.employees_multicheck.get_checked_options().length === 0) {
            frappe.throw({
                message: __("Please select the employees you want to mark attendance for."),
                title: __("Mandatory")
            });
        }

        if (!frm.doc.status) {
            frappe.throw({
                message: __("Please select the attendance status."),
                title: __("Mandatory")
            });
        }
        
        const marked_employees = frm.employees_multicheck.get_checked_options();

        frappe.call({
            method: "digitz_hr.digitz_hrms.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance_for_whole_month",
            args: {
                employee_list: marked_employees,
                employee_code: frm.doc.employee_code,
                status: frm.doc.status,
                date: frm.doc.date,
                late_entry: frm.doc.late_entry,
                early_exit: frm.doc.early_exit,
            },
            freeze: true,
            freeze_message: __("Marking Attendance")
        }).then((r) => {
            if (!r.exc) {
                
                frm.refresh();
            }
        });
    },
});
