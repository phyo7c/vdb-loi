from odoo import models, fields, api, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round, date_utils, convert_file, html2plaintext, is_html_empty, format_amount

class HRPaySlip(models.Model):
    _inherit = 'hr.payslip'

    currency_rate = fields.Float('Currency Rate')
    previous_income = fields.Float('Previous Income', compute='_compute_previous_amount', store=True)
    previous_tax_paid = fields.Float('Previous Tax Paid', compute='_compute_previous_amount', store=True)
    remaining_months = fields.Integer('Remaining Months', compute='_compute_previous_amount', store=True)
    badge_id = fields.Integer('Badge ID', compute='_get_employee_id', store=True)

    @api.depends('employee_id')
    def _get_employee_id(self):
        for rec in self:
            rec.badge_id = int(rec.employee_id.barcode)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_previous_amount(self):
        for slip in self:
            prev_income = slip.employee_id.pre_income_total
            prev_tax_paid = slip.employee_id.pre_tax_paid
            remaining_months = 0
            total_months = 12
            today = fields.Date.today()
            fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', slip.date_to),
                                                                  ('date_to', '>=', slip.date_to),
                                                                  ('company_id', '=', slip.employee_id.company_id.id)])
            print("_compute_previous_amount>>>", fiscal_year, slip.date_to)
            if fiscal_year:
                remaining_months = relativedelta(fiscal_year.date_to, slip.date_to).months
                if slip.employee_id.joining_date and fiscal_year.date_from < slip.employee_id.joining_date < fiscal_year.date_to:
                    prev_income = slip.employee_id.pre_income_total
                    prev_tax_paid = slip.employee_id.pre_tax_paid
                if slip.employee_id.joining_date and slip.employee_id.joining_date > fiscal_year.date_from:
                    total_months = 12 - relativedelta(slip.employee_id.joining_date, fiscal_year.date_from).months
                payslips = self.env['hr.payslip'].sudo().search([('employee_id', '=', slip.employee_id.id),
                                                                 ('date_to', '>=', fiscal_year.date_from),
                                                                 ('date_to', '<=', fiscal_year.date_to),
                                                                 ('state', 'not in', ('draft', 'cancel'))])
                for pay in payslips:
                    slipline_obj = self.env['hr.payslip.line']
                    basic = slipline_obj.sudo().search([('slip_id', '=', pay.id), ('code', '=', 'NET')])
                    # deductions = slipline_obj.search([('slip_id', '=', pay.id), ('code', 'in', ('UNPAID', 'SSB'))])
                    deductions = slipline_obj.sudo().search([('slip_id', '=', pay.id), ('code', '=', 'DEDUCTION')])
                    tax_paid = slipline_obj.sudo().search([('slip_id', '=', pay.id), ('code', '=', 'PIT')])
                    absents = slipline_obj.sudo().search([('slip_id', '=', pay.id), ('code', '=', 'ABSENCE')])
                    prev_income += basic and basic.total or 0
                    prev_income -= sum([abs(ded.total) for ded in deductions])
                    prev_income -= sum([abs(dedabs.total) for dedabs in absents])
                    prev_tax_paid += tax_paid and tax_paid.total or 0

            #sunday_unpaid = self._get_sunday_list(slip.employee_id, slip.date_from, slip.date_to)
            slip.remaining_months = remaining_months
            slip.previous_income = prev_income
            slip.previous_tax_paid = prev_tax_paid
            #slip.total_months = total_months
            #slip.sunday_unpaid = 0  # sunday_unpaid
            #slip.half_month_day = 0
            if slip.employee_id.joining_date and (
                    datetime.strptime(str(slip.employee_id.joining_date), '%Y-%m-%d').strftime(
                        "%Y-%m") == datetime.strptime(str(slip.date_from), '%Y-%m-%d').strftime("%Y-%m")):
                delta = slip.date_to - slip.employee_id.joining_date
                slip.half_month_day = delta.days + 1
            elif slip.employee_id.resign_date and (
                    datetime.strptime(str(slip.employee_id.resign_date), '%Y-%m-%d').strftime(
                        "%Y-%m") == datetime.strptime(str(slip.date_from), '%Y-%m-%d').strftime("%Y-%m")):
                delta = slip.employee_id.resign_date - slip.date_from
                #slip.half_month_day = delta.days + 1
                remaining_months = relativedelta(slip.date_to, slip.employee_id.resign_date).months
                slip.total_months = relativedelta(slip.date_to, fiscal_year.date_from).months
                slip.remaining_months = remaining_months
                

    def _get_payslip_lines(self):
        line_vals = []
        for payslip in self:
            inverse_company_rate = 0
            rate = self.env['res.currency.rate'].search([('currency_id', '=', payslip.payslip_currency_id.id), ('name', '<=', date.today())], order="id desc", limit=1)
            if rate:
                inverse_company_rate = rate.inverse_company_rate
                payslip.write({"currency_rate": inverse_company_rate})
            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules'].dict
            result_rules_dict = localdict['result_rules'].dict

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                if rule.id in blacklisted_rule_ids:
                    continue
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100,
                    'result_name': False
                })
                if rule._satisfy_condition(localdict):
                    amount, qty, rate = rule._compute_rule(localdict)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                    # Retrieve the line name in the employee's lang
                    employee_lang = payslip.employee_id.sudo().address_home_id.lang
                    # This actually has an impact, don't remove this line
                    context = {'lang': employee_lang}
                    if localdict['result_name']:
                        rule_name = localdict['result_name']
                    elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION', 'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
                        if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
                            if rule.name == "Double Holiday Pay":
                                rule_name = _("Double Holiday Pay")
                            if rule.struct_id.name == "CP200: Employees 13th Month":
                                rule_name = _("Prorated end-of-year bonus")
                            else:
                                rule_name = _('Basic Salary')
                        elif rule.code == "GROSS":
                            rule_name = _('Gross')
                        elif rule.code == "DEDUCTION":
                            rule_name = _('Deduction')
                        elif rule.code == "REIMBURSEMENT":
                            rule_name = _('Reimbursement')
                        elif rule.code == 'NET':
                            rule_name = _('Net Salary')
                    else:
                        rule_name = rule.with_context(lang=employee_lang).name
                    # create/overwrite the rule in the temporary results
                    result[rule.code] = {
                        'sequence': rule.sequence,
                        'code': rule.code,
                        'name': rule_name,
                        'note': html2plaintext(rule.note) if not is_html_empty(rule.note) else '',
                        'salary_rule_id': rule.id,
                        'contract_id': localdict['contract'].id,
                        'employee_id': localdict['employee'].id,
                        'amount': amount,
                        'quantity': qty,
                        'rate': rate,
                        'slip_id': payslip.id,
                    }
            line_vals += list(result.values())
        return line_vals

class HRPaySlipLine(models.Model):
    _inherit = 'hr.payslip.line'

    company_currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
