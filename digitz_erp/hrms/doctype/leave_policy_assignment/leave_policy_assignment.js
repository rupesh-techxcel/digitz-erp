// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Policy Assignment", {
    onload(frm) {
      assign_defaults(frm);
  
      frm.set_query('leave_policy', function() {
              return {
                  filters: {
                      "docstatus": 1
                  }
              };
          });    
      },
  
    assignment_based_on: function(frm) {
          if (frm.doc.assignment_based_on) {
              frm.events.set_effective_date(frm);
          } else {
              frm.set_value("effective_from", '');
              frm.set_value("effective_to", '');
          }
      },
  
      leave_period: function(frm) {
          if (frm.doc.leave_period) {
              frm.events.set_effective_date(frm);
          }
      },
  
      set_effective_date: function(frm) {
          if (frm.doc.assignment_based_on == "Leave Period" && frm.doc.leave_period) {
              frappe.model.with_doc("Leave Period", frm.doc.leave_period, function () {
                  let from_date = frappe.model.get_value("Leave Period", frm.doc.leave_period, "from_date");
                  let to_date = frappe.model.get_value("Leave Period", frm.doc.leave_period, "to_date");
                  frm.set_value("effective_from", from_date);
                  frm.set_value("effective_to", to_date);
  
              });
          } else if (frm.doc.assignment_based_on == "Joining Date" && frm.doc.employee) {
              frappe.model.with_doc("Employee", frm.doc.employee, function () {
                  let from_date = frappe.model.get_value("Employee", frm.doc.employee, "date_of_joining");
                  frm.set_value("effective_from", from_date);
                  frm.set_value("effective_to", frappe.datetime.add_months(frm.doc.effective_from, 12));
              });
          }
          frm.refresh();
      },
      leave_policy:function(frm)
      {
          frm.clear_table('leave_allocations')
  
          frappe.call({
              method: '.get_leave_policy_details',
              args: {
                  leave_policy: frm.doc.leave_policy
              },
              callback: function(r) {
                  if (r.message) {
                      // Create a set of existing employee IDs in the child table
                      let existing_leave_types = new Set(frm.doc.leave_allocations.map(row => row.leave_type));
  
                      // Iterate through the result and add each employee to the child table if not already present
                      r.message.forEach(function(leave_policy) {
                          if (!existing_leave_types.has(leave_policy.leave_type)) {
                              let child = frm.add_child('leave_allocations');
                              child.leave_type = leave_policy.leave_type;
                              child.annual_allocation = leave_policy.annual_allocation;
                          }
                      });
  
                      // Refresh the child table to reflect changes
                      frm.refresh_field('leave_allocations');				
                  }
              }
          });
      },
      get_employees: function(frm) {
          if (!frm.doc.designation) {
              frappe.msgprint("Select Designation");
          } else if (!frm.doc.leave_period) {
              frappe.msgprint("Select Leave Period");
          } else {
              frappe.call({
                  method: '.get_employees_for_leave_policy',
                  args: {
                      designation: frm.doc.designation,
                      leave_period: frm.doc.leave_period
                  },
                  callback: function(r) {
                      if (r.message) {
                          // Create a set of existing employee IDs in the child table
                          let existing_employees = new Set(frm.doc.leave_policy_employees.map(row => row.employee));
  
                          // Iterate through the result and add each employee to the child table if not already present
                          r.message.forEach(function(leave_policy_employee) {
                              if (!existing_employees.has(leave_policy_employee.employee)) {
                                  let child = frm.add_child('leave_policy_employees');
                                  child.employee = leave_policy_employee.employee;
                                  child.employee_name = leave_policy_employee.employee_name;
                                  child.designation = leave_policy_employee.designation;
                                  child.department = leave_policy_employee.department;
                              }
                          });
  
                          // Refresh the child table to reflect changes
                          frm.refresh_field('leave_policy_employees');
                      }
                  }
              });
          }
      }
  });
  
  function assign_defaults(frm)
  {
      if(frm.is_new())
      {
          
      }
   }
  