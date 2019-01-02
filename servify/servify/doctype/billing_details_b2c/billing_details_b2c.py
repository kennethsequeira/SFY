# -*- coding: utf-8 -*-
# Copyright (c) 2018, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class BillingDetailsB2C(Document):
	def validate(self):
		if self.is_deferred and not (self.start_date and self.end_date):
			frappe.throw(_("Start Date and End Date is required for deferred processing"))

		if not self.sold_plan_id and not self.service_request_id:
			frappe.throw(_("Sold Plan ID or Service Request ID is mandatory for processing"))

		if (not self.base_value and self.base_value != 0.0) or (not self.total and self.total != 0.0):
			frappe.throw(_("Base value and total are mandatory"))

		if self.base_value > 0.0 and self.sold_plan_id:
			invoices = frappe.db.sql('''select sold_plan_id, name
											from `tabBilling Details B2C`
											where sold_plan_id = %s
											and name != %s
											and base_value > 0
										''', (self.sold_plan_id, self.name) , as_dict=1)
			for invoice in invoices:
				if invoice["sold_plan_id"]:
					frappe.throw(_("Sold Plan ID {0} already exists for record {1}".format(invoice["sold_plan_id"], invoice["name"])))

		if self.reference_payment_order or self.invoice_number:
			pass
		else:
			frappe.throw(_("Invoice Number or Reference Payment Order is mandatory to upload transactions"))

		if not self.state_code:
			frappe.throw(_("State Code is mandatory to upload transactions"))

		si = frappe.db.sql('''select distinct b.parent
								from `tabSales Invoice` a, `tabSales Invoice Item` b
							where
								a.name = b.parent
								and b.sold_plan_id = %(sold_plan_id)s
								and a.is_return = 0
								and a.docstatus < 2''', {
									"sold_plan_id": self.sold_plan_id
								})
		if si:
			si = si[0][0]
			frappe.throw(_("Sold Plan ID {0} already exists in Sales Invoice {1}".format(self.sold_plan_id, si)))