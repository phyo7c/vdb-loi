from odoo import api, fields, models, _
import json
import math
from num2words import num2words
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "hr.employee"

    def _get_payslip(self,month):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == 'NET':
                        return line_id.total
                        break
            else:
                return 0.0

    def _get_payslip2(self,month):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',self.id)])
        for payslip_id in payslip_ids:
            m = payslip_id.date_from.month
            if m > 0 and m == month:
                for line_id in payslip_id.line_ids:
                    if line_id.code == 'PIT':
                        return line_id.total
                        break
            else:
                return 0.0


    def _get_parents(self):
        f = m = 0
        if self.tax_exemption_father:
            f = 1
        if self.tax_exemption_mother:
            m = 1
        return f+m

