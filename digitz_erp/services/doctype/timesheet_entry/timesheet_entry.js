// Copyright (c) 2024,   and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timesheet Entry", {

    show_a_message: function (frm, message) {
      frappe.call({
        method: 'digitz_erp.api.settings_api.show_a_message',
        args: {
          msg: message
        }
      });
    },
  
    onload: function (frm) {
      if (frm.is_new()) {
        frm.events.get_default_company_and_warehouse(frm);
        // frm.events.show_a_message(frm, "Select date and Submit the document to start execution.");
      }
    },
  
    setup: function (frm) {
      frm.fields_dict.time_sheet_entry_details.grid.get_field('employee').get_query = () => {
        return {
          filters: {
            disabled: 0
          }
        };
      };
    },
  
    refresh: function (frm) {
      if (frm.doc.work_order) {
        frm.set_df_property('work_order', 'read_only', 1);
        frm.set_df_property('project', 'read_only', 1);
        frm.set_df_property('boq', 'read_only', 1);
        frm.set_df_property('boq_execution', 'read_only', 1);
      }  
      else if (frm.doc.project)
      {
        frm.set_df_property('project', 'read_only', 1);
      }  
      create_custom_buttons(frm)
    },
  
    edit_posting_date_and_time: function (frm) {
      const readOnly = frm.doc.edit_posting_date_and_time ? 0 : 1;
      frm.set_df_property("posting_date", "read_only", readOnly);
      frm.set_df_property("posting_time", "read_only", readOnly);
    },
  
    get_default_company_and_warehouse: function (frm) {
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Global Settings",
          fieldname: "default_company",
        },
        callback: (r) => {
          default_company = r.message.default_company
          frm.set_value("company", r.message.default_company);
  
          frappe.call(
            {
              method: 'frappe.client.get_value',
              args: {
                'doctype': 'Company',
                'filters': { 'company_name': default_company },
                'fieldname': ['default_warehouse', 'rate_includes_tax','default_work_in_progress_account','default_labour_cost_payable_account']
              },
              callback: (r2) => {
                
                frm.set_value("work_in_progress_account",r2.message.default_work_in_progress_account)
                frm.set_value("labour_cost_payable_account",r2.message.default_labour_cost_payable_account)
                
                frm.refresh_field("work_in_progress_account");
                frm.refresh_field("labour_cost_payable_account");
              }
            });
  
        }
      });
    },
  
    work_order: function (frm) {
      if (frm.doc.work_order) {
        frappe.call({
          method: 'digitz_erp.api.boq_api.create_timesheet_entry',
          args: {
            work_order: frm.doc.work_order
          },
          callback: function (r) {
            if (r.message) {
              frm.set_value('project', r.message.project);
              frm.set_value('work_order', r.message.work_order);
              frm.set_value('boq_execution', r.message.boq_execution);
              frm.set_value('boq', r.message.boq);
            } else {
              frappe.msgprint('No work order found.');
            }
          }
        });
      }
    },
    project: function (frm) {
      // Check if work_order is not defined
      if (frm.doc.work_order != undefined) {
          return; // Exit the function if work_order is not set
      }
  
      //Check if project is selected
      if (frm.doc.project) {
          frappe.call({
              method: 'digitz_erp.api.boq_api.get_project_details',
              args: {
                  project: frm.doc.project
              },
              callback: function (r) {
                  if (r.message) {
                      frm.set_value('boq', r.message.boq);
                      frm.set_value('boq_execution', r.message.boq_execution);
                  } else {
                      frappe.msgprint('No BOQ or BOQ Execution found for the selected project.');
                  }
              }
          });
      }
  },
  
  });
  
  frappe.ui.form.on('Timesheet Entry Detail', {
    employee: function (frm, cdt, cdn) {
      let row = frappe.get_doc(cdt, cdn);
  
      // Check if project is selected
      if (!frm.doc.project) {
          frappe.model.set_value(cdt, cdn, "employee", "");
          frappe.throw("Please select a project to enter employee time.");
      }
  
      // Fetch employee document and get rate_per_hour
      if (row.employee) {
        frappe.call({
          method: "frappe.client.get_value",
          args: {
            doctype: "Employee",
            fieldname: "per_hour_rate",
            filters: { name: row.employee }
          },
          callback: function (r) {
            if (r.message) {
              frappe.model.set_value(cdt, cdn, "per_hour_rate", r.message.per_hour_rate);
            } else {
              frappe.msgprint("Rate per hour not found for the selected employee.");
            }
          }
        });
      }
  
      // Fetch default shift values
      get_employee_shift_default_values(frm, cdt, cdn);
  
      // Set project and work_order fields in the row
      frappe.model.set_value(cdt, cdn, "project", frm.doc.project);
      frappe.model.set_value(cdt, cdn, "work_order", frm.doc.work_order);
  
      calculate_total_worked_hours(frm, cdt, cdn);
    },
  from_time: function(frm, cdt, cdn) {
     calculate_total_worked_hours(frm, cdt, cdn);
     console.log("re-calculated")
  },
  to_time: function(frm, cdt, cdn) {
      calculate_total_worked_hours(frm, cdt, cdn);
      console.log("re-calculated")
  },
  break_in_minutes: function(frm, cdt, cdn) {
     calculate_total_worked_hours(frm, cdt, cdn);
     console.log("re-calculated")
  },
  pickup_time_in_minutes: function(frm, cdt, cdn) {
     calculate_total_worked_hours(frm, cdt, cdn);
     console.log("re-calculated")
  }
  
  });
  
  function get_employee_shift_default_values(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    let employee = row.employee;
  
    if (employee) {
      frappe.call({
        method: 'digitz_erp.api.employee_api.validate_employee_shift',
        args: {
          employee: employee,
          shift_date: frm.doc.timesheet_date
        },
        callback: (r) => {
          if (r.message === false) {
            frappe.throw("Shift not allocated for the employee. Shift Allocation mandatory as per HR Settings.");
          } else {
            frappe.call({
              method: 'digitz_erp.api.employee_api.get_employee_shift',
              args: {
                employee: employee,
                shift_date: frm.doc.timesheet_date
              },
              callback: (r) => {
                let shift = r.message[0];
                let shift_allocation = r.message[1];
  
                frappe.model.set_value(cdt, cdn, 'shift', shift.name);
                frappe.model.set_value(cdt, cdn, 'from_time', shift.start_time);
                frappe.model.set_value(cdt, cdn, 'to_time', shift.end_time);
                frappe.model.set_value(cdt, cdn, 'standard_working_hours', shift.standard_working_hours);
                frappe.model.set_value(cdt, cdn, 'break_in_minutes', shift.break_in_minutes);
                frappe.model.set_value(cdt, cdn, 'pickup_time_in_minutes', shift.pickup_time_in_minutes);
                frappe.model.set_value(cdt, cdn, 'overtime_1_slab', shift.overtime_1_slab);
                
                if (shift.ot_applicable) {
                  frappe.model.set_value(cdt, cdn, 'overtime_applicable', true);
                  frappe.model.set_value(cdt, cdn, 'overtime_1_percentage', shift.overtime_rate_percentage);
                  frappe.model.set_value(cdt, cdn, 'overtime_2_percentage', shift.overtime_2_rate_percentage);
                  frappe.model.set_value(cdt, cdn, 'holiday_overtime_percentage', shift.holiday_overtime_percentage);
                }
  
                if (shift_allocation) {
                  frappe.model.set_value(cdt, cdn, 'to_time', shift_allocation.expected_end_time);
                }
              }
            });
          }
        }
      });
    }
  }
  
  let create_custom_buttons = function(frm){
      if (frappe.user.has_role('Management')) {
          if(!frm.is_new() && (frm.doc.docstatus == 1)){
        frm.add_custom_button('General Ledgers',() =>{
          general_ledgers(frm)
        }, 'Postings');	
          }
      }
  }
  
  // Function to calculate total minutes from "HH:mm" time string
  function timeToMinutes(timeString) {
    const [hours, minutes] = timeString.split(':').map(Number);
    return hours * 60 + minutes;
  }
  
  function calculate_total_worked_hours(frm) {
    let totalLabourCost = 0;
    let totalCostWithoutOvertime = 0;
    let totalCostForOvertime = 0;
  
    // Loop through all rows in the child table
    frm.doc.time_sheet_entry_details.forEach(row => {
        // Ensure from_time, to_time, standard_working_hours, and per_hour_rate are present
        if (!row.from_time || !row.to_time || !row.standard_working_hours || !row.per_hour_rate) {
            row.total_worked_hours = 0;
            row.cost_without_overtime = 0;
            row.overtime_1 = 0;
            row.overtime_2 = 0;
            row.cost_for_overtime = 0;
            row.labour_cost = 0;
            return;
        }
  
        // Convert `from_time` and `to_time` to total minutes
        let fromTimeMinutes = timeToMinutes(row.from_time);
        let toTimeMinutes = timeToMinutes(row.to_time);
        let totalMinutes = toTimeMinutes - fromTimeMinutes;
  
        // Deduct break and pickup times if provided
        let breakMinutes = row.break_in_minutes || 0;
        let pickupMinutes = row.pickup_time_in_minutes || 0;
        let netWorkedMinutes = totalMinutes - breakMinutes - pickupMinutes;
  
        // If net worked minutes are negative, set it to zero and show a message
        if (netWorkedMinutes < 0) {
            frappe.msgprint("The combined break and pickup time exceeds the total worked hours.");
            netWorkedMinutes = 0;
        }
  
        // Convert net worked minutes to hours
        let worked_hours = netWorkedMinutes / 60;
        row.worked_hours = Math.round(worked_hours * 100) / 100; // Round to 2 decimal places
  
        // Calculate regular hours cost
        let regularHoursCost = worked_hours <= row.standard_working_hours
            ? worked_hours * row.per_hour_rate
            : row.standard_working_hours * row.per_hour_rate;
        row.cost_without_overtime = Math.round(regularHoursCost * 100) / 100; // Round to 2 decimal places
  
        // Overtime calculation
        if (row.overtime_applicable) {
            let excessHours = worked_hours - row.standard_working_hours;
  
            if (excessHours > 0) {
                // Determine overtime hours based on slabs
                let overtimeSlab1Hours = Math.min(excessHours, row.overtime_1_slab || 0);
                let overtimeSlab2Hours = Math.max(0, excessHours - overtimeSlab1Hours);
                console.log("excessHours",excessHours)
                console.log("overtimeSlab1Hours",overtimeSlab1Hours)
                console.log("overtimeSlab2Hours",overtimeSlab2Hours)
  
  
                row.overtime_1 = Math.round(overtimeSlab1Hours * 100) / 100; // Round to 2 decimal places
                row.overtime_2 = Math.round(overtimeSlab2Hours * 100) / 100; // Round to 2 decimal places
  
                // Calculate overtime amounts
                let overtime1Amount = row.overtime_1 * row.per_hour_rate * (row.overtime_1_percentage / 100);
                let overtime2Amount = row.overtime_2 * row.per_hour_rate * (row.overtime_2_percentage / 100);
  
                row.overtime_1_amount = overtime1Amount
                row.overtime_2_amount = overtime2Amount 
                row.cost_for_overtime = Math.round((overtime1Amount + overtime2Amount) * 100) / 100; // Round to 2 decimal places
            } else {
                // If no excess hours, set overtime fields and amounts to 0
                row.overtime_1 = 0;
                row.overtime_2 = 0;
                row.cost_for_overtime = 0;
            }
        } else {
            // If overtime is not applicable, set overtime fields and amounts to 0
            row.overtime_1 = 0;
            row.overtime_2 = 0;
            row.cost_for_overtime = 0;
        }
  
        // Calculate total labour cost for this row
        row.labour_cost = row.cost_without_overtime + row.cost_for_overtime;
  
        // Aggregate costs for the parent document
        totalLabourCost += row.labour_cost;
        totalCostWithoutOvertime += row.cost_without_overtime;
        totalCostForOvertime += row.cost_for_overtime;
    });
  
    // Update the parent document with total costs
    frm.set_value('labour_cost', totalLabourCost);
    frm.set_value('cost_without_overtime', totalCostWithoutOvertime);
    frm.set_value('cost_for_overtime', totalCostForOvertime);
  
    console.log("totalLabourCost", totalLabourCost)
    console.log("cost_without_overtime", totalCostWithoutOvertime)
    console.log('cost_for_overtime', totalCostForOvertime);
  
    frm.refresh_field('timesheet_entry_details');
  }
  
  
  let general_ledgers = function (frm) {
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_gl_postings",
        args: {
            voucher: frm.doc.doctype,
            voucher_no: frm.doc.name
        },
        callback: function (response) {
            let gl_postings = response.message.gl_postings;
            let totalDebit = parseFloat(response.message.total_debit).toFixed(2);
            let totalCredit = parseFloat(response.message.total_credit).toFixed(2);
  
            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 680px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 15%;">Account</th>' +
                '<th style="width: 25%;">Remarks</th>' +
                              '<th style="width: 10%;">Debit Amount</th>' +
                              '<th style="width: 10%;">Credit Amount</th>' +
                '<th style="width: 10%;">Party</th>' +
                              '<th style="width: 10%;">Against Account</th>' +                              
                              '<th style="width: 10%;">Project</th>' +
                              '<th style="width: 10%;">Cost Center</th>' +                              
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';
  
      console.log("gl_postings",gl_postings)
  
            gl_postings.forEach(function (gl_posting) {
                let remarksText = gl_posting.remarks || '';
                let debitAmount = parseFloat(gl_posting.debit_amount).toFixed(2);
                let creditAmount = parseFloat(gl_posting.credit_amount).toFixed(2);
  
                htmlContent += '<tr>' +
                               `<td>${gl_posting.account}</td>` +
                 `<td>${remarksText}</td>` +
                               `<td style="text-align: right;">${debitAmount}</td>` +
                               `<td style="text-align: right;">${creditAmount}</td>` +
                 `<td>${gl_posting.party}</td>` +
                               `<td>${gl_posting.against_account}</td>` +                               
                               `<td>${gl_posting.project}</td>` +
                               `<td>${gl_posting.cost_center}</td>` +
                               
                               '</tr>';
            });
  
            // Add totals row
            htmlContent += '<tr>' +
                           '<td style="font-weight: bold;">Total</td>' +
               '<td></td>'+
                           `<td style="text-align: right; font-weight: bold;">${totalDebit}</td>` +
                           `<td style="text-align: right; font-weight: bold;">${totalCredit}</td>` +
                           '<td colspan="5"></td>' +
                           '</tr>';
  
            htmlContent += '</tbody></table></div>';
  
            // Create and show the dialog
            let d = new frappe.ui.Dialog({
                title: 'General Ledgers',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'general_ledgers_html',
                    options: htmlContent
                }],
                primary_action_label: 'Close',
                primary_action: function () {
                    d.hide();
                }
            });
  
            // Set custom width for the dialog
            d.$wrapper.find('.modal-dialog').css('max-width', '90%'); 
  
            d.show();
        }
    });
  };
    
    