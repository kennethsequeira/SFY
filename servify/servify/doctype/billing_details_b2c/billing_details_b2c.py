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

		if self.base_value > 0 and self.sold_plan_id:
			invoices = frappe.db.sql('''select sold_plan_id
											from `tabBilling Details B2C`
											where sold_plan_id = %s
											and base_value > 0
										''', self.sold_plan_id, as_dict=1)
			for invoice in invoices:
				if invoice["sold_plan_id"]:
					frappe.throw(_("Sold Plan ID {0} already exists".format(invoice["sold_plan_id"])))