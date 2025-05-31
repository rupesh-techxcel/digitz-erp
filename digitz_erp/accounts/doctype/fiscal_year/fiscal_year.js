// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fiscal Year", {
	refresh(frm) {

	},
    year_name:function(frm)
    {
        setYearDates(frm)
    }
});

function setYearDates(frm) {

    const year = frm.doc.year_name; // Assuming `year` is the input field in your form

    if (!year || isNaN(year) || year < 1) {
        frappe.msgprint(__('Please enter a valid year.'));
        return;
    }

    // Calculate the start and end dates of the year
    const startDate = `${year}-01-01`;
    const endDate = `${year}-12-31`;

    // Set the calculated values to the respective fields
    frm.set_value('year_start_date', startDate);
    frm.set_value('year_end_date', endDate);
    
}

