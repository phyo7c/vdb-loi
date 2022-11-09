from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ssb_not_calculation = fields.Boolean('SSB not Calculation')
    over_60_ssb = fields.Boolean('Over 60 SSB')
    over_60_ssb_percent = fields.Float('Over 60 SSB Percent')
    ssb_no = fields.Char('SSB Number')
    ssb_issue_date = fields.Date('SSB Card Issued Date')
