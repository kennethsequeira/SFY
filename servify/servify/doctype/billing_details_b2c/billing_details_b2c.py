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
