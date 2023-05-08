frappe.ready(function () {
	frappe.web_form.on('customer', (field, value) => {
		fetch("/api/resource/Customer/" + value).then(async doc => {
			var res_json = await doc.json();
			frappe.web_form.set_value("customer_address", res_json.data.full_address)
			frappe.web_form.set_value("salesman", res_json.data.salesman)
			frappe.web_form.set_value("tax_id", res_json.data.tax_id)
			frappe.web_form.set_value("credit_days", res_json.data.credit_days)
		})
	});
})