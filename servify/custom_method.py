from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr
from frappe import _

def create_sales_b2b():
	invoices = frappe.db.sql('''select name, posting_date, customer, customer_name,
		 							customer_address, taxes_and_charges,
									customer_gstin, billing_address_gstin, place_of_supply
									from `tabBilling Customer`
									where sales_invoice not in 
									(select legacy_invoice_no 
									from `tabSales Invoice`
									where legacy_invoice_no is not NULL)''',as_dict=1)

	for invoice in invoices:
		si_doc = frappe.new_doc("Sales Invoice")
		si_doc.company = "Service Lee Technologies Pvt Ltd"
		si_doc.currency = frappe.db.get_value("Company", si_doc.company, "default_currency")
		si_doc.customer = invoice["customer"]
		si_doc.set_posting_time = 1
		si_doc.posting_date = invoice["posting_date"]
		si_doc.due_date = invoice["posting_date"]
		si_doc.customer_name = invoice["customer_name"]
		si_doc.customer_address = invoice["customer_address"]
		si_doc.shipping_address_name = invoice["customer_address"]
		si_doc.customer_gstin = invoice["customer_gstin"]
		si_doc.billing_address_gstin = invoice["billing_address_gstin"]
		si_doc.place_of_supply = invoice["place_of_supply"]
		si_doc.company_address = "Service Lee Technologies Pvt Ltd-Billing"
		si_doc.company_gstin = "27AAVCS8563N1Z4"
		#set template
		if invoice["taxes_and_charges"] in ["Out of State GST @ 18%","Out of State GST - 12%"]:
			si_doc.taxes_and_charges = "Out of State GST - SLTPL"
		if invoice["taxes_and_charges"] in ["In State GST @ 18%","In State GST @ 12%"]:
			si_doc.taxes_and_charges = "In State GST - SLTPL"

		si_doc.legacy_invoice_no = invoice["name"]
		invoice_details = frappe.db.sql('''select sold_plan_id, plan_id, 
										start_date, end_date,
										base_value, project
										from `tabBilling Details`
										where sales_invoice = %s''',invoice["name"],
										as_dict=1)
		details_exist = False
		for detail in invoice_details:
			if detail["base_value"] < 0:
				qty = -1
				detail["base_value"] = invoice["base_value"] * -1
				si_doc.is_return = 1
			else:
				qty = 1

			si_doc.append("items", {
				"item_code": detail["plan_id"],
				"qty": qty,
				"rate": detail["base_value"],
				"sold_plan_id": detail["sold_plan_id"],
				"enable_deferred_revenue": 1,
				"service_start_date": detail["start_date"],
				"service_end_date": detail["end_date"]
			})
			si_doc.project = detail["project"]
			details_exist = True
			
		if invoice["taxes_and_charges"] == "In State GST @ 18%":
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "SGST - SLTPL",
				"description": "SGST @ 9%",
				"rate": 9
			})
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "CGST - SLTPL",
				"description": "CGST @ 9%",
				"rate": 9
			})

		if invoice["taxes_and_charges"] == "In State GST @ 12%":
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "SGST - SLTPL",
				"description": "SGST @ 6%",
				"rate": 6
			})
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "CGST - SLTPL",
				"description": "CGST @ 6%",
				"rate": 6
			})

		if invoice["taxes_and_charges"] == "Out of State GST @ 18%":
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "IGST - SLTPL",
				"description": "IGST @ 18%",
				"rate": 18
			})

		if invoice["taxes_and_charges"] == "Out of State GST - 12%":
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "IGST - SLTPL",
				"description": "IGST @ 12%",
				"rate": 12
			})

		si_doc.set_missing_values()
		si_doc.flags.ignore_mandatory = True
		if details_exist:
			si_doc.insert(ignore_permissions=True)

def create_sales_b2c():
	invoices = frappe.db.sql('''select sold_plan_id, plan_id, customer_name, customer_address,
									project, posting_date, invoice_number,
									plan_purchase_date, start_date, end_date, base_value,
									cgst_amount, sgst_amount, igst_amount, total, sales_invoice, state_code,
									customer_gstin, reference_payment_order, cost_center, service_request_id
									from `tabBilling Details B2C`
									where invoice_number not in 
									(select legacy_invoice_no
									from `tabSales Invoice` 
									where legacy_invoice_no is not NULL)
								''',as_dict=1)

	for invoice in invoices:
		si_doc = frappe.new_doc("Sales Invoice")
		si_doc.company = "Service Lee Technologies Pvt Ltd"
		si_doc.currency = frappe.db.get_value("Company", si_doc.company, "default_currency")
		si_doc.customer = invoice["customer_name"]
		si_doc.set_posting_time = 1
		si_doc.posting_date = invoice["posting_date"]
		si_doc.due_date = invoice["posting_date"]
		si_doc.customer_name = invoice["customer_name"]
		si_doc.customer_address = invoice["customer_address"]
		si_doc.shipping_address_name = invoice["customer_address"]
		si_doc.project = invoice["project"]
		si_doc.company_address = "Service Lee Technologies Pvt Ltd-Billing"
		si_doc.company_gstin = "27AAVCS8563N1Z4"
		si_doc.place_of_supply = invoice["state_code"]
		si_doc.customer_gstin = invoice["customer_gstin"]
		#logic for this
		if invoice["cgst_amount"] > 0 or invoice["sgst_amount"] > 0:
			si_doc.taxes_and_charges = "In State GST - SLTPL"

		if invoice["igst_amount"] > 0:
			si_doc.taxes_and_charges = "Out of State GST - SLTPL"
		si_doc.legacy_invoice_no = invoice["invoice_number"]

		if invoice["base_value"] < 0:
			qty = -1
			invoice["base_value"] = invoice["base_value"] * -1
			invoice["cgst_amount"] = invoice["cgst_amount"] * -1
			invoice["sgst_amount"] = invoice["sgst_amount"] * -1
			invoice["igst_amount"] = invoice["igst_amount"] * -1
			si_doc.is_return = 1
		else:
			qty = 1

		si_doc.append("items", {
			"item_code": invoice["plan_id"],
			"qty": qty,
			"rate": invoice["base_value"],
			"sold_plan_id": invoice["sold_plan_id"],
			"enable_deferred_revenue": 1,
			"service_start_date": invoice["start_date"],
			"service_end_date": invoice["end_date"],
			"reference_payment_order": invoice["reference_payment_order"],
			"cost_center": invoice["cost_center"],
			"service_request_id": invoice["service_request_id"]
		})
		if invoice["cgst_amount"] > 0 or invoice["sgst_amount"] > 0:
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "05010012 - Output SGST - SLTPL",
				"description": "SGST @ 9%",
				"rate": 9
			})
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "05010011 - Output CGST - SLTPL",
				"description": "CGST @ 9%",
				"rate": 9
			})

		if invoice["igst_amount"] > 0:
			si_doc.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": "05010010 - Output IGST - SLTPL",
				"description": "IGST @ 18%",
				"rate": 18
			})

		si_doc.set_missing_values()
		si_doc.flags.ignore_mandatory = True

		try:
			if invoice["plan_id"]:
				si_doc.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(message=e, title="Create Sales Invoice")


		frappe.db.sql('''update `tabSales Invoice` a set a.place_of_supply = (select max(b.state_code)
																				from `tabBilling Details B2C` b
																				where b.invoice_number = a.legacy_invoice_no
																				and b.state_code IS NOT NULL)
								where a.name = %s''',si_doc.name)

def create_jv():
	jes = frappe.db.sql('''select 
								distinct legacy_voucher, posting_date 
						from
							`tabServify Ledger`
						order by legacy_voucher, posting_date asc''', as_dict = 1)

	for je in jes:
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.company = "Service Lee Technologies Pvt Ltd"
		je_doc.voucher_type = "Journal Entry"
		je_doc.cheque_no = je["legacy_voucher"]
		je_doc.posting_date = je["posting_date"]
		je_doc.cheque_date = je["posting_date"]

		je_details = frappe.db.sql('''select 
								 			account, debit, credit, party, party_name, 
											CONCAT(ifnull(reference, " "), "/", ifnull(narration, " "), "/", ifnull(item, " ")) as "remark" 
									from
										`tabServify Ledger`
									where 
										legacy_voucher = %s and posting_date = %s
									order by legacy_voucher asc''', (je["legacy_voucher"], je["posting_date"]), as_dict = 1)

		for jed in je_details:
			if jed["account"][:2] in ["01","02", "03"]:
				cost_center = "Main - SLTPL"
			else:
				cost_center = ""

			je_doc.append("accounts", {
				"account": jed["account"],
				"cost_center": cost_center,
				"party_type": jed["party"],
				"party": jed["party_name"],
				"debit_in_account_currency": jed["debit"],
				"debit":jed["debit"],
				"credit_in_account_currency":jed["credit"],
				"credit":jed["credit"],
				"user_remark": jed["remark"]
			})

		if je["legacy_voucher"]:
			je_doc.insert(ignore_permissions=True)

def submit_si():
	invoices = frappe.db.sql('''select name
								from `tabSales Invoice`
								where status = 0''',as_dict=1)

	for invoice in invoices:
		si = frappe.get_doc("Sales Invoice", invoice["name"])
		si.submit()

def update_sold_plan_id():
	prev_name = ""

	sold_plan_ids = frappe.db.sql('''select distinct sitm.name, sp.service_stop_date, sitm.parent, sp.name as "spupd_name"
										from `tabSold Plan Update` sp, `tabSales Invoice Item` sitm, `tabSales Invoice` si
										where sp.sales_invoice IS NULL
										and sp.sold_plan_id = sitm.sold_plan_id
										and sitm.enable_deferred_revenue = 1
										and sp.service_stop_date >= sitm.service_start_date
										and sp.service_stop_date <= sitm.service_end_date
										and sitm.service_stop_date is NULL
										and sp.company = si.company
										and si.docstatus = 1
										and si.name = sitm.parent''', as_dict=1)

	for sold_plan_id in sold_plan_ids:
		si_item = frappe.get_doc('Sales Invoice Item', sold_plan_id["name"])
		si_item.service_stop_date = sold_plan_id["service_stop_date"]
		si_item.save()

		if sold_plan_id["spupd_name"]:
			if prev_name != sold_plan_id["spupd_name"]:
				spupd = frappe.get_doc('Sold Plan Update', sold_plan_id["spupd_name"])
				spupd.sales_invoice = sold_plan_id["parent"]
				spupd.save()
				prev_name = sold_plan_id["spupd_name"]

def validate_unique_sold_plan_id(self, method):
	#default letter head for Sales Invoice
	self.letter_head = "Service Lee Technologies Pvt Ltd"
	for d in self.items:
		if d.sold_plan_id and d.qty > 0:
			si = frappe.db.sql('''select distinct b.parent
									from `tabSales Invoice` a, `tabSales Invoice Item` b
								where
									a.name = b.parent
									and b.sold_plan_id = %(sold_plan_id)s
									and a.name != %(parent)s
									and a.is_return = 0
									and a.docstatus < 2''', {
										"sold_plan_id": d.sold_plan_id,
										"parent": d.parent
									})
			if si:
				si = si[0][0]
				frappe.throw(_("Sold Plan ID {0} already exists in Sales Invoice {1}".format(d.sold_plan_id, si)))