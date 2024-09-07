// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
        
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
        }
    }
});

function toggle_planning_table(frm) {
    if (!frm.doc.planning_id) {
        frm.get_field('planning').grid.wrapper.hide();
        console.log("Planning table hidden");
    } else {
        frm.get_field('planning').grid.wrapper.show();
        console.log("Planning table shown");
    }
    frm.refresh_field('planning');
}


