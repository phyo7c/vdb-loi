from odoo import fields, models


class PublicHolidays(models.Model):
    _name = 'hr.public.holidays'
    _description = 'Public Holidays'
    _rec_name = 'year'

    year = fields.Char('Calendar Year')
    company_id = fields.Many2one('res.company', string='Company')
    holiday_line = fields.One2many('public.holidays.line', 'line_id', string='Public Holidays')


class PublicHolidaysLine(models.Model):
    _name = 'public.holidays.line'

    line_id = fields.Many2one('hr.public.holidays', string='Public Holidays', index=True, required=True, ondelete='cascade')
    date = fields.Date('Date')
    name = fields.Char('Name')
    variable = fields.Boolean('Date May Change', dafault=False)
    type = fields.Selection([('holiday', 'Holiday'), ('working', 'Working Day')], string='Holiday Type', default='holiday')
