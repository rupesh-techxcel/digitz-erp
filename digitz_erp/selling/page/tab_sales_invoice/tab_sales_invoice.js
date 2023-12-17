frappe.pages['tab-sales-invoice'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tab Sales Invoice',
		single_column: true
	});
}