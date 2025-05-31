// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.shift_name) {
            get_shift_allocation_count(frm, frm.doc.shift_name);
        }
    },
    onload(frm) {
        if (frm.is_new()) {
            get_ot_settings(frm);
        }
    },
    setup(frm) {
        frm.set_query("default_shift", function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
    },
});

function get_ot_settings(frm) {

    console.log("from get_ot_settings")

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "HR Settings",
            name: "HR Settings"
        },
        callback: function(response) {
            if (response.message) {
                const hr_settings = response.message;
               
                // Assign fields from HR Settings to the current Shift form
                frm.set_value("ot_applicable", hr_settings.overtime_applicable);
                frm.set_value("overtime_rate_percentage", hr_settings.ot_slab_1_percentage);
                frm.set_value("overtime_2_rate_percentage", hr_settings.ot_slab_2_percentage);
                frm.set_value("overtime_1_slab", hr_settings.overtime_1_slab);
                frm.set_value("holiday_overtime_percentage", hr_settings.holiday_ot_percentage);

                // Overtime field should be visible only if it is enabled in the HR settings
                frm.toggle_display("ot_applicable", hr_settings.overtime_applicable);
            }
        }
    });
}

function get_shift_allocation_count(frm, shift) {
    if (!shift) {
        console.warn("Shift name is required to get the allocation count.");
        return;
    }

    frappe.call({
        method: 'digitz_erp.api.employee_api.get_shift_allocation_count',
        args: {
            shift_name: shift
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('shift_allocation_count', r.message);
            }
        }
    });
}
