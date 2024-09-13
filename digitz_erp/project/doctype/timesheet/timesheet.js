// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
    frm.set_query("task", "planning", function (doc, cdt, cdn) {
      var d = locals[cdt][cdn]

      return {
          "filters": {
              "service": frm.doc.service || ""
          }
      }
  })
	},
    onload(frm){
        if(frm.is_new())
            {
                default_company = "";
                frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': 'Global Settings',
                    'fieldname': 'default_company'
                },
                callback: (r) => {
                    default_company = r.message.default_company
                    frm.set_value('company',default_company);
                    frm.refresh_field("company")
                }
                });
            }
    },
    
});

frappe.ui.form.on('Timesheet', {
    refresh: function(frm) {
        toggle_planning_table(frm);
        frm.add_custom_button(('Mark Attendance'), function(){
            mark_attendance_automatically(frm);
        });
    },
    planning_id: function(frm) {
        toggle_planning_table(frm);
        if(frm.doc.planning_id){
            console.log("Planning ID changed to:", frm.doc.planning_id);
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Planning',
                    name: frm.doc.planning_id
                },
                callback: function(r) {
                    if(r.message) {
                        console.log("Received planning data:", r.message);
                        let planning = r.message;
                        frm.clear_table('planning');
                        
                        if (Array.isArray(planning.table_mjoz) && planning.table_mjoz.length > 0) {
                            planning.table_mjoz.forEach(function(plan) {
                                let row = frm.add_child('planning');
                                row.employee = plan.employee;
                                row.shift= plan.shift;
                                row.start_time = plan.start_time;
                                row.end_time = plan.end_time;
                                row.task= plan.task;
                                console.log("Added row:", row);
                            });
                            frm.refresh_field('planning');
                            console.log("Planning table refreshed");
                        } else {
                            console.log("No planning details found in table_mjoz");
                            frappe.msgprint("No planning details found for this Planning ID.");
                        }
                    } else {
                        console.log("No data received from server");
                        frappe.msgprint("Unable to fetch planning data. Please check the Planning ID.");
                    }
                },
                error: function(err) {
                    console.error("Error fetching planning data:", err);
                    frappe.msgprint("Error fetching planning data. Please check the console for details.");
                }
            });
        } else {
            console.log("Planning ID cleared");
            frm.clear_table('planning');
            frm.refresh_field('planning');
        }
    }
});

function toggle_planning_table(frm) {
  if (frm.doc.planning_id) {
      frm.get_field('planning').grid.wrapper.show();
  } else {
      frm.get_field('planning').grid.wrapper.show();
  }
  frm.refresh_field('planning');
}



function mark_attendance_automatically(frm){
    all_rows(frm)
}

// function all_rows(frm){
//     frm.doc.planning.forEach(function(row){
//         frappe.call({
//             method:'digitz_erp.project.doctype.timesheet.timesheet.create_Attendance',
//             args:{
//                 employee:row.employee,
//                 shift: frm.doc.shift
//             },
//             callback: function(r){
//                 if(r.message){
//                     frappe.msgprint("Done")
//                 }
//             }
//         })
//         // frappe.new_doc('Attendance',{
//         //     employee: row.employee,
//         //     shift: frm.doc.shift,
//         // });
//     })
// }
function all_rows(frm) {
    frm.doc.planning.forEach(function(row) {
      if (row.employee) {
        if (row.is_present) {
          frappe.call({
            method: "frappe.desk.form.save.savedocs",
            args: {
              doc: {
                doctype: "Attendance",
                employee: row.employee,
                shift: frm.doc.shift,
                attendance_status: "Present",
                attendance_start_time: row.start_time,
                attendance_end_time:row.end_time,
              },
              action: "Submit"
            },
            callback: function(r) {
              if (!r.exc) {
                console.log('Attendance submitted for employee:', row.employee);
              } else {
                console.error('Failed to submit attendance for employee:', row.employee);
              }
            }
          });
        } else {
          frappe.call({
            method: "frappe.desk.form.save.savedocs",
            args: {
              doc: {
                doctype: "Attendance",
                employee: row.employee,
                shift: frm.doc.shift,
                attendance_start_time: frappe.datetime.now_time(),
                attendance_end_time:frappe.datetime.now_time(),
                attendance_status: "Absent"
              },
              action: "Save"
            },
            callback: function(r) {
              if (!r.exc) {
                console.log('Attendance submitted for employee:', row.employee);
              } else {
                console.error('Failed to submit attendance for employee:', row.employee);
              }
            }
          });
        }
      } else {
        console.error('Employee field is missing for a row in the planning table.');
      }
    });
  }