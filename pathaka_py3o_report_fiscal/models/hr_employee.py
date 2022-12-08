from odoo import api, fields, models, _
import json
import math
from num2words import num2words
from odoo.exceptions import UserError
import locale

MONTH_SELECTION = [
    ('1', 'ဇန်နဝါရီ'),
    ('2', 'ဖေဖော်ဝါရီ'),
    ('3', 'မတ်'),
    ('4', 'ဧပြီ'),
    ('5', 'မေ'),
    ('6', 'ဇွန်'),
    ('7', 'ဇူလိုင်'),
    ('8', 'သြဂုတ်'),
    ('9', 'စက်တင်ဘာ'),
    ('10', 'အောက်တိုဘာ'),
    ('11', 'နိုဝင်ဘာ'),
    ('12', 'ဒီဇင်ဘာ'),
]


class AccountMove(models.Model):
    _inherit = "hr.employee"

    def get_month_list(self, i, month):
        data = int(month)
        check = data + i - 2
        if check > 11:
            return MONTH_SELECTION[check - 12][0]
        else:
            return MONTH_SELECTION[check][0]

    def _get_payslip(self, i, month, fiscal, code):
        month = int(self.get_month_list(i, month))
        payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', self.id),
                                                     ('date_to', '>', fiscal.date_from),
                                                     ('date_to', '<', fiscal.date_to)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_to.month
            total = 0
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == code:
                        total = round(line_id.total, 2)
                        total = f"{total:,}"
                        split_num = total.split(".")
                        if len(split_num) >= 2:
                            if len(split_num[1]) == 1:
                                total = total+'0'
                        return total
                        break
            else:
                return 0.0
        return 0.0

    def _get_batches_tax_no(self, i, month, fiscal):
        month = int(self.get_month_list(i, month))
        payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', self.id),
                                                     ('date_to', '>', fiscal.date_from),
                                                     ('date_to', '<', fiscal.date_to)])
        tax_approve = ' '
        for payslip_id in payslip_ids:
            m = payslip_id.date_to.month
            if m == month:
                tax_approve = payslip_id.payslip_run_id.tax_approval_no
        return tax_approve

    def _get_total(self, fiscal, code):
        payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', self.id),
                                                     ('date_to', '>', fiscal.date_from),
                                                     ('date_to', '<', fiscal.date_to)])
        total = 0.00
        for payslip_id in payslip_ids:
            m = payslip_id.date_to.month
            for line_id in payslip_id.line_ids:
                if line_id.code == code:
                    total += line_id.total
        if total > 0:
            total = round(total, 2)
            total = f"{total:,}"
            split_num = total.split(".")
            if len(split_num) >= 2:
                if len(split_num[1]) == 1:
                    total = total + '0'
        return total

    def _get_parents(self):
        f = m = 0
        if self.tax_exemption_father:
            f = 1
        if self.tax_exemption_mother:
            m = 1
        return f+m

    def _get_premium_fee(self):
        total = round(self.insurance_amt, 2)
        total = f"{total:,}"
        split_num = total.split(".")
        if len(split_num) >= 2:
            if len(split_num[1]) == 1:
                total = total + '0'
        return total

    def _get_ssb_fee(self):
        total = round(12 * 6000, 2)
        total = f"{total:,}"
        split_num = total.split(".")
        if len(split_num) >= 2:
            if len(split_num[1]) == 1:
                total = total + '0'
        return total

    def _get_basic_allowance(self, fiscal):
        payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', self.id),
                                                     ('date_to', '>', fiscal.date_from),
                                                     ('date_to', '<', fiscal.date_to)])
        total = 0.00
        for payslip_id in payslip_ids:
            for line_id in payslip_id.line_ids:
                if line_id.code == '20P':
                    total += line_id.total
        if total > 0:
            total = round(total, 2)
            total = f"{total:,}"
            split_num = total.split(".")
            if len(split_num) >= 2:
                if len(split_num[1]) == 1:
                    total = total + '0'
        return total
