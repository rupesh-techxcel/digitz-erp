frappe.views.calendar['Purchase Order'] = {
    field_map: {
        start: 'due_date',
        end: 'due_date',
        id: 'name',
        allDay: 1, // All-day event, set to 1
        title: 'name',
        status: 'order_status',
        color: 'green'
    },
    style_map: {
        Completed: 'success', // Define the styles for different statuses
        Partial: 'info',
        Pending: 'danger'
        // Add more styles and statuses as needed
    },
    get_events_method: 'digitz_erp.api.purchase_order_api.get_purchase_order_due_dates'     
};