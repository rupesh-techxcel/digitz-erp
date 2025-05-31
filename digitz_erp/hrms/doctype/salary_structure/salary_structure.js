// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Structure", {
	refresh(frm) {

	},
    setup(frm){

        frm.set_query("fetch_from_a_template", function () {
			return {
				"filters": {
					"disabled": 0                    
				}
			};
		});

        frm.set_query('component', 'earnings', () => {
            return {
                filters: {
                    type: 'Earning'
                }
            }
          });

          frm.set_query('component', 'deductions', () => {
            return {
                filters: {
                    type: 'Deduction'
                }
            }
          });
    },
    fetch_from_a_template: function(frm) {

        console.log("Fetching from template:", frm.doc.fetch_from_a_template);
    
        if (frm.doc.fetch_from_a_template) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Salary Structure Template',
                    name: frm.doc.fetch_from_a_template
                },
                callback: function(response) {
                    if (response.message) {
                        const linked_doc = response.message;
                        console.log("Linked document:", linked_doc);
    
                        // Clear the existing child tables
                        frm.clear_table("earnings");
                        frm.clear_table("deductions");
    
                        // Add earnings from the linked document
                        if (linked_doc.earnings) {
                            $.each(linked_doc.earnings, function(i, row) {
                                let child = frm.add_child("earnings");
                                child.component = row.component;
                                child.abbrevation = row.abbrevation;
                                child.amount = row.amount;
                                console.log("Adding earning:", child);
                            });
                        } else {
                            console.log("No earnings found in the linked document.");
                        }
    
                        // Add deductions from the linked document
                        if (linked_doc.deductions) {
                            $.each(linked_doc.deductions, function(i, row) {
                                let child = frm.add_child("deductions");
                                child.component = row.component;
                                child.abbrevation = row.abbrevation;
                                child.amount = row.amount;
                                console.log("Adding deduction:", child);
                            });
                        } else {
                            console.log("No deductions found in the linked document.");
                        }
    
                        frm.refresh_field("earnings");
                        frm.refresh_field("deductions");
                    } else {
                        console.log("No response message received.");
                    }
                }
            });
        } else {
            console.log("fetch_from_a_template is not set.");
        }
    },
    get_employees: function(frm) {
        if (!frm.doc.designation) {
            frappe.msgprint("Select Designation");
        } else {
            frappe.call({
                method: 'digitz_erp.api.employee_api.get_employees_in_designation',
                args: {
                    designation: frm.doc.designation
                },
                callback: function(r) {
                    if (r.message) {
                        // Create a set of existing employee IDs in the child table
                        let existing_employees = new Set(frm.doc.salary_structure_assignment.map(row => row.employee));

                        // Iterate through the result and add each employee to the child table if not already present
                        r.message.forEach(function(employee) {
                            if (!existing_employees.has(employee.employee)) {
                                let child = frm.add_child('salary_structure_assignment');
                                child.employee = employee.employee;
                                child.employee_name = employee.employee_name;
                                child.designation = employee.designation;
                                child.department = employee.department;
                                child.from_date = frm.doc.from_date;
                                child.overtime_rate = frm.doc.overtime_rate
                                child.holiday_rate = frm.doc.holiday_rate
                            }
                        });

                        // Refresh the child table to reflect changes
                        frm.refresh_field('salary_structure_assignment');
                    } else {
                        frappe.msgprint("No employees found for the selected designation.");
                    }
                }
            });
        }
    }
    
});

frappe.ui.form.on("Salary Structure Assignment", {

    employee(frm,cdt,cdn)
    {
        var row= locals[cdt][cdn];

        row.holiday_rate = frm.doc.holiday_rate
        row.overtime_rate = frm.doc.overtime_rate
    }

});