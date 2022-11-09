from odoo import models, fields, api, _
from datetime import date, datetime


class HRPaySlip(models.Model):
    _inherit = 'hr.payslip'

    payslip_currency_id = fields.Many2one('res.currency', string='Currency', related='contract_id.currency_id')
    salary = fields.Float('Salary', compute='_compute_salary', readonly=True)

    @api.onchange('contract_id')
    def _onchange_contract(self):
        if self.contract_id:
            self.payslip_currency_id = self.contract_id.currency_id
            if self.contract_id.currency_id != self.company_id.currency_id:
                currency = self.env['res.currency'].browse(self.contract_id.currency_id.id)
                rate = self.env['res.currency.rate'].search([('currency_id', '=', currency.id), ('name', '<=', date.today())], order="id desc", limit=1)
                self.salary = self.contract_id.wage * rate.inverse_company_rate
            else:
                self.salary = self.contract_id.wage

    @api.depends('contract_id')
    def _compute_salary(self):
        if self.contract_id:
            if self.contract_id.currency_id != self.payslip_currency_id:
                currency = self.env['res.currency'].browse(self.contract_id.currency_id.id)
                rate = self.env['res.currency.rate'].search([('currency_id', '=', currency.id), ('name', '<=', date.today())], order="id desc", limit=1)
                self.salary = self.contract_id.wage * rate.inverse_company_rate
            else:
                self.salary = self.contract_id.wage
        else:
            self.salary = 0

    @api.depends('contract_id')
    def _compute_normal_wage(self):
        with_contract = self.filtered('contract_id')
        (self - with_contract).normal_wage = 0
        for payslip in with_contract:
            if with_contract.payslip_currency_id != self.company_id.currency_id:
                wage = payslip._get_contract_wage()
                currency = self.env['res.currency'].browse(with_contract.payslip_currency_id.id)
                rate = self.env['res.currency.rate'].search([('currency_id', '=', currency.id),('name', '<=', date.today())], order="id desc", limit=1)
                payslip.normal_wage = wage * rate.inverse_company_rate
            else:
                payslip.normal_wage = payslip._get_contract_wage()
