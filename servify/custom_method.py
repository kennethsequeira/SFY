from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr
from frappe import _
from frappe.model.mapper import get_mapped_doc

def create_sales_b2b():
	invoices = frappe.db.sql('''select name, posting_date, customer, customer_name,
		 							customer_address, taxes_and_charges,
									customer_gstin, billing_address_gstin, place_of_supply,
									project
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
		si_doc.sfy_place_of_supply = invoice["place_of_supply"]
		si_doc.company_address = "Service Lee Technologies Pvt Ltd-Billing"
		si_doc.company_gstin = "27AAVCS8563N1Z4"
		si_doc.project = invoice["project"]
		si_doc.legacy_invoice_no = invoice["sales_invoice"]
		#set template
		if invoice["taxes_and_charges"] in ["Out of State GST @ 18%","Out of State GST - 12%"]:
			si_doc.taxes_and_charges = "Out of State GST - SLTPL"
		if invoice["taxes_and_charges"] in ["In State GST @ 18%","In State GST @ 12%"]:
			si_doc.taxes_and_charges = "In State GST - SLTPL"

		si_doc.legacy_invoice_no = invoice["name"]
		invoice_details = frappe.db.sql('''select sold_plan_id, plan_id, 
										start_date, end_date,
										base_value, cost_center, is_deferred
										from `tabBilling Details`
										where sales_invoice = %s''',invoice["name"],
										as_dict=1)
		details_exist = False
		for detail in invoice_details:
			if detail["base_value"] < 0:
				qty = -1
				detail["base_value"] = detail["base_value"] * -1
				si_doc.is_return = 1
			else:
				qty = 1

			si_doc.append("items", {
				"item_code": detail["plan_id"],
				"qty": qty,
				"rate": detail["base_value"],
				"sold_plan_id": detail["sold_plan_id"],
				"enable_deferred_revenue": detail["is_deferred"],
				"service_start_date": detail["start_date"],
				"service_end_date": detail["end_date"],
				"cost_center": detail["cost_center"]
			})
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

		try:
			if details_exist:
				si_doc.insert(ignore_permissions=True)

		except Exception as e:
			error_string = "B2B Sales" + invoice["sales_invoice"]
			frappe.log_error(message = e, title = error_string)

def create_sales_b2c():
	invoices = frappe.db.sql('''select sold_plan_id, plan_id, customer_name, customer_address,
									project, posting_date, invoice_number,
									plan_purchase_date, start_date, end_date, base_value,
									cgst_amount, sgst_amount, igst_amount, total, sales_invoice, state_code,
									customer_gstin, reference_payment_order, cost_center, service_request_id,
									is_deferred, name
									from `tabBilling Details B2C`
									where name not in 
									(select transaction_reference
									from `tabSales Invoice` 
									where transaction_reference is not NULL)
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
		si_doc.reference_payment_order = invoice["reference_payment_order"]
		si_doc.transaction_reference = invoice["name"]
		si_doc.sfy_place_of_supply = invoice["state_code"]
		if invoice["base_value"] < 0:
			si_doc.naming_series = "SFY/CN/18-19/E.########"
		else:
			si_doc.naming_series = "SFY/18-19/E.########"

		#logic for this
		if invoice["cgst_amount"] > 0 or invoice["sgst_amount"] > 0:
			si_doc.taxes_and_charges = "In State GST - SLTPL"

		if invoice["igst_amount"] > 0:
			si_doc.taxes_and_charges = "Out of State GST - SLTPL"
		si_doc.legacy_invoice_no = invoice["invoice_number"]

		if invoice["base_value"] < 0:
			qty = -1
			invoice["base_value"] = invoice["base_value"] * -1
			si_doc.is_return = 1
		else:
			qty = 1
		if invoice["is_deferred"]:
			si_doc.append("items", {
				"item_code": invoice["plan_id"],
				"qty": qty,
				"rate": invoice["base_value"],
				"sold_plan_id": invoice["sold_plan_id"],
				"service_start_date": invoice["start_date"],
				"service_end_date": invoice["end_date"],
				"reference_payment_order": invoice["reference_payment_order"],
				"cost_center": invoice["cost_center"],
				"service_request_id": invoice["service_request_id"]
			})
		else:
			si_doc.append("items", {
				"item_code": invoice["plan_id"],
				"qty": qty,
				"rate": invoice["base_value"],
				"sold_plan_id": invoice["sold_plan_id"],
				"reference_payment_order": invoice["reference_payment_order"],
				"cost_center": invoice["cost_center"],
				"service_request_id": invoice["service_request_id"]
			})

		if invoice["cgst_amount"] > 0 or invoice["sgst_amount"] > 0 or invoice["cgst_amount"] < 0 or invoice["sgst_amount"] < 0:
			si_doc.append("taxes", {
				"charge_type": "Actual",
				"account_head": "05010012 - Output SGST - SLTPL",
				"description": "SGST",
				"tax_amount": invoice["sgst_amount"]
			})
			si_doc.append("taxes", {
				"charge_type": "Actual",
				"account_head": "05010011 - Output CGST - SLTPL",
				"description": "CGST",
				"tax_amount": invoice["cgst_amount"]
			})

		if invoice["igst_amount"] > 0 or invoice["igst_amount"] < 0:
			si_doc.append("taxes", {
				"charge_type": "Actual",
				"account_head": "05010010 - Output IGST - SLTPL",
				"description": "IGST",
				"tax_amount": invoice["igst_amount"]
			})

		si_doc.set_missing_values()
		si_doc.flags.ignore_mandatory = True

		try:
			if invoice["plan_id"] or invoice["service_request_id"]:
				si_doc.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(message=e, title="Create Sales Invoice B2C")

def create_jv():
	jes = frappe.db.sql('''select 
								distinct legacy_voucher, posting_date 
						from
							`tabServify Ledger`
						order by legacy_voucher, posting_date asc''', as_dict = 1)

	count = 0

	for je in jes:
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.company = "Service Lee Technologies Pvt Ltd"
		je_doc.voucher_type = "Journal Entry"
		je_doc.cheque_no = je["legacy_voucher"]
		je_doc.posting_date = je["posting_date"]
		je_doc.cheque_date = je["posting_date"]

		je_details = frappe.db.sql('''select 
								 			ledger, debit, credit, customer, supplier, employee, shareholder
											CONCAT(ifnull(reference, " "), "/", ifnull(narration, " "), "/", ifnull(item, " ")) as "remark" 
									from
										`tabServify Ledger`
									where 
										legacy_voucher = %s and posting_date = %s
									order by legacy_voucher asc''', (je["legacy_voucher"], je["posting_date"]), as_dict = 1)

		for jed in je_details:
			if jed["ledger"][:2] in ["01","02", "03"]:
				cost_center = "Main - SLTPL"
			else:
				cost_center = ""

			if jed["ledger"] in ["03001001", "03001002", "03001003", "03001004"]:
				cost_center = "Corporate - SLTPL"

			if jed["customer"]:
				party = "Customer"
				party_name = jed["customer"]

			if jed["supplier"]:
				party = "Supplier"
				party_name = jed["supplier"]

			if jed["employee"]:
				party = "Employee"
				party_name = jed["employee"]

			if jed["shareholder"]:
				party = "Shareholder"
				party_name = jed["shareholder"]

			je_doc.append("accounts", {
				"account": jed["ledger"],
				"cost_center": cost_center,
				"party_type": party,
				"party": party_name,
				"debit_in_account_currency": jed["debit"],
				"debit":jed["debit"],
				"credit_in_account_currency":jed["credit"],
				"credit":jed["credit"],
				"user_remark": jed["remark"]
			})

		try:
			if je["legacy_voucher"]:
				je_doc.insert(ignore_permissions=True)


		except Exception as e:
			frappe.log_error(message=e, title="JV Error" + je["legacy_voucher"] + je["posting_date"])

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
	if not self.letter_head:
		self.letter_head = "Service Lee Technologies Pvt Ltd"
	if not self.sfy_is_repair:
		for d in self.items:
			if d.sold_plan_id and d.qty > 0:
				si = frappe.db.sql('''select distinct b.parent
										from `tabSales Invoice` a, `tabSales Invoice Item` b
									where
										a.name = b.parent
										and b.sold_plan_id = %(sold_plan_id)s
										and a.name != %(parent)s
										and a.is_return = 0
										and a.sfy_is_repair = 0
										and a.docstatus < 2''', {
											"sold_plan_id": d.sold_plan_id,
											"parent": d.parent
										})
				if si:
					si = si[0][0]
					frappe.throw(_("Sold Plan ID {0} already exists in Sales Invoice {1}".format(d.sold_plan_id, si)))

	if self.sfy_place_of_supply:
		self.place_of_supply = self.sfy_place_of_supply

def default_manager_name(self, method):
	if self.reports_to:
		reports_to_name = frappe.db.sql('''select 
												employee_name, company_email
											from
												`tabEmployee`
											where name = %s''', self.reports_to)
		if reports_to_name:
			self.sfy_reports_to_name = reports_to_name[0][0]
			self.sfy_report_to_email = reports_to_name[0][1]

def validate_goal_setting(self, method):
	#Default information based on employee ID
	if self.employee:
		employee_defaults = frappe.db.sql('''select 
													employee_name, company_email, department, branch, reports_to
												from
													`tabEmployee`
												where name = %s''', self.employee)

		if employee_defaults:
			self.full_name = employee_defaults[0][0]
			self.employee_email = employee_defaults[0][1]
			self.department = employee_defaults[0][2]
			self.branch = employee_defaults[0][3]

			if employee_defaults[0][4]:
				reports_to_email = frappe.db.sql('''select 
														company_email
													from
														`tabEmployee`
													where name = %s''', employee_defaults[0][4])
				if reports_to_email:
					self.manager = employee_defaults[0][4]
					self.manager_email = reports_to_email[0][0]

			if employee_defaults[0][2]:
				department_appraiser = frappe.db.sql('''select 
															appraisal_approver
														from
															`tabDepartment`
														where name = %s''', employee_defaults[0][2])
				self.department_head_email = department_appraiser[0][0]
	#validate weights
	kra_weight = 0
	beh_kra_weight = 0

	for kra in self.kra:
		if flt(kra.weightage) < 5 or flt(kra.weightage) > 30:
			frappe.throw(_("KRA weights should be between 5 and 30"))
		kra_weight += kra.weightage

	for beh_kra in self.behavioral_assesment:
		beh_kra_weight += beh_kra.weightage

	if kra_weight != 100:
		frappe.throw(_("Sum of KRA weights should be 100"))

	if beh_kra_weight != 100:
		frappe.throw(_("Sum of Behavioral KRA weights should be 100"))	

def validate_appraisal(self, method):
	#validate make appraisal from goal setting
	if not self.quarter:
		frappe.throw(_("Please select the quarter for which you want to make appraisal for"))

	if self.goal_setting_ref:
		#validate quarterly only one
		appraisal = frappe.db.sql('''select name
								from 
									`tabServify Appraisal`
								where 
									employee = %s 
									and goal_setting_ref = %s 
									and quarter =  %s
									and name != %s
									and (docstatus = 1 or docstatus = 0)''',
									(self.employee, self.goal_setting_ref, self.quarter, self.name))
		if appraisal:
			frappe.throw(_("Appraisal {0} already exists for the quarter {1} and Goal Setting {2}".format(appraisal[0][0], self.quarter, self.goal_setting_ref)))
	else:
		frappe.throw(_("Appraisal needs to be made from Goal Setting Document"))
	#validate weights
	kra_weight = 0
	beh_kra_weight = 0
	
	for kra in self.kra:
		if flt(kra.weightage) < 5 or flt(kra.weightage) > 30:
			frappe.throw(_("KRA weights should be between 5 and 30"))
		kra_weight += kra.weightage

	for beh_kra in self.behavioral_assesment:
		beh_kra_weight += beh_kra.weightage

	if kra_weight != 100:
		frappe.throw(_("Sum of KRA weights should be 100"))

	if beh_kra_weight != 100:
		frappe.throw(_("Sum of Behavioral KRA weights should be 100"))
	#calculate weighted average
	kra_score_earned = 0
	for d in self.get('kra'):
		if d.man_rating:
			kra_score_earned += flt(d.man_rating) * flt(d.weightage) / 100

	if kra_score_earned > 0:
		self.overall_kra_rating = kra_score_earned
	
	beh_score_earned = 0
	for d in self.get('behavioral_assesment'):
		if d.man_rating:
			beh_score_earned += flt(d.man_rating) * flt(d.weightage) / 100

	if beh_score_earned > 0:
		self.overall_beh_rating = beh_score_earned

	#get weightage
	kra_weightage = 0
	kra_weightage = frappe.db.get_single_value('Servify HR Settings', 'sfy_kra_weightage')
	beh_weightage = 0
	beh_weightage = 100 - flt(kra_weightage)

	if (self.overall_kra_rating + self.overall_beh_rating) > 0:
		self.overall_rating = (flt(self.overall_kra_rating) * flt(kra_weightage) / 100) + (flt(self.overall_beh_rating) * flt(beh_weightage) / 100)

@frappe.whitelist()
def make_appraisal(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.goal_setting_ref = source.name
		target.naming_series = "ACC-APPRAISAL-.YYYY.-"

	doclist = get_mapped_doc("Goal Setting Template", source_name,{
				"Goal Setting Template": {
					"doctype": "Servify Appraisal",
				},
				"Goal Setting KRA": {
					"doctype": "Appraisal KRA"
				},
				"Goal Setting Behavioral": {
					"doctype": "Appraisal Behavioral"
				}
		}, target_doc, set_missing_values)

	return doclist