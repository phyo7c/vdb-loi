from odoo import api, fields, models, _
import json
import math
from num2words import num2words
from odoo.exceptions import UserError
import locale


class AccountMove(models.Model):
    _inherit = "hr.employee"

    def _get_payslip(self,month,decimal: int = 2):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            total = 0
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == 'NET':
                        total = round(line_id.total, 2)
                        total = f"{total:,}"
                        split_num = total.split(".")
                        if len(split_num) >= 2:
                            if len(split_num[1]) == 1:
                                total = total+'0'
                        return total

            else:
                return 0.00

    def _get_payslip_internal(self,month):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == 'NET':
                        return line_id.total

            else:
                return 0.00

    def _get_payslip2(self,month):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == 'PIT':
                        total = round(line_id.total, 2)
                        total = f"{total:,}"
                        split_num = total.split(".")
                        if len(split_num) >= 2:
                            if len(split_num[1]) == 1:
                                total = total + '0'
                        return total

            else:
                return 0.00

    def _get_payslip2_internal(self,month):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == 'PIT':
                        return line_id.total

            else:
                return 0.00


    def _get_total(self):
        total = 0
        for x in range(1, 13):
            total += self._get_payslip_internal(x)
        total = round(total, 2)
        total = f"{total:,}"
        split_num = total.split(".")
        if len(split_num) >= 2:
            if len(split_num[1]) == 1:
                total = total + '0'
        return total

    def _get_total2(self):
        total = 0
        for x in range(1, 13):
            total += self._get_payslip2_internal(x)
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
        return self.insurance_amt

    def _get_ssb_fee(self):
        return (12 * 6000)

    def _get_basic_allowance(self):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            if m > 0:
                for line_id in payslip_id.line_ids:
                    if line_id.code == '20P':
                        total = round(line_id.total, 2)
                        total = f"{total:,}"
                        return total

            else:
                return 0.00


