from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr
from frappe import _
from frappe.model.mapper import get_mapped_doc

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