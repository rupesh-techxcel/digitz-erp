// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Holiday List", {
	refresh(frm) {

	},   
    
    from_date:function(frm)
    {

        if (frm.doc.from_date) {
            // Get the year from the from_date
            let fromDate = new Date(frm.doc.from_date);
            let year = fromDate.getFullYear();
            
            let endDate = new Date(year, 11, 31); // December is 11 (0-indexed)
            endDate.setHours(12); // Set the time to noon to avoid timezone issues

            frm.set_value('to_date', endDate.toISOString().split('T')[0]); // Format date as YYYY-MM-DD
        }
    },
    add_to_holidays:function(frm)
    {

        if (!frm.doc.holiday_name || !frm.doc.holiday_date) {
            frappe.msgprint(__('Please enter Holiday Name and Date'));
            return;
        }

        // Clear existing entries in holidays with the same date
        frm.doc.holidays = frm.doc.holidays.filter(holiday => holiday.date !== frm.doc.holiday_date);

        // Add new holiday entry
        let new_holiday = frm.add_child('holidays');
        new_holiday.date = frm.doc.holiday_date;
        new_holiday.holiday_name = frm.doc.holiday_name
        new_holiday.description = frm.doc.holiday_name;
        new_holiday.weekly_holiday = '';

        frm.refresh_field('holidays');
        frappe.msgprint(__('Holiday added successfully'));
    },
    add_weekly_off_to_holidays: function(frm) {
        if (!frm.doc.weekly_off || !frm.doc.from_date || !frm.doc.to_date) {
            frappe.msgprint(__('Please select Weekly Off, From Date, and To Date'));
            return;
        }

        const weeklyOffMap = {
            'Sunday': 0,
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5,
            'Saturday': 6
        };

        const fromDate = new Date(frm.doc.from_date);
        const toDate = new Date(frm.doc.to_date);
        const selectedWeeklyOff = weeklyOffMap[frm.doc.weekly_off];

        // Clear existing entries in holidays
        frm.clear_table('holidays');

        let currentDate = new Date(fromDate);
        while (currentDate <= toDate) {
            if (currentDate.getDay() === selectedWeeklyOff) {
                let holiday = frm.add_child('holidays');
                holiday.date = currentDate.toISOString().split('T')[0]; // Format date as YYYY-MM-DD
                holiday.holiday_name = 'Weekly Off';
                holiday.weekly_off = frm.doc.weekly_off;
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }

        frm.refresh_field('holidays');
        frappe.msgprint(__('Holidays added successfully'));
    }
});
