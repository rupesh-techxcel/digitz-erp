// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Planning", {
	refresh(frm) {
        frm.add_custom_button("Create Timesheet",function(){
            frappe.new_doc('Timesheet',{
                planning_id:frm.doc.name
            })
        })
	},
});

frappe.ui.form.on('Planning', {
    refresh: function(frm) {
        console.log("Planning form refreshed");
    },
    
    project: function(frm) {
        console.log("Project changed to:", frm.doc.project);
        frm.set_query("task", "table_mjoz", function() {
            return {
                filters: {
                    "project": frm.doc.project
                }
            };
        });
        console.log("Task filter set for project:", frm.doc.project);
    },
    
    before_save: function(frm) {
        console.log("Before saving Planning doc");
        // This will re-apply the filter before saving, just in case
        frm.set_query("task", "table_mjoz", function() {
            return {
                filters: {
                    "project": frm.doc.project
                }
            };
        });
    }
});

frappe.ui.form.on('PlanningChildDC', {
    table_mjoz_add: function(frm, cdt, cdn) {
        console.log("New row added to table_mjoz");
        frm.set_query("task", "table_mjoz", function() {
            return {
                filters: {
                    "project": frm.doc.project
                }
            };
        });
        console.log("Task filter applied to new row");
    }
});
