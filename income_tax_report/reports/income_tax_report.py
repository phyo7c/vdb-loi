# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class HrEmployeeIncomeTaxReport(models.AbstractModel):
    _name = 'report.income_tax_report.report_income_tax'
    _description = 'Income Tax Report'

    def _get_header_info(self, fiscal_year_id):
        return {
            'fiscal_year': fiscal_year_id[1],
            'fiscal_year_id': fiscal_year_id[0],
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        income_tax_report = self.env['ir.actions.report']._get_report_from_name('income_tax_report.report_income_tax')
        employees = self.env['hr.employee'].browse(data['form']['emp'])
        return {
            'doc_ids': self.ids,
            'doc_model': income_tax_report.model,
            'docs': employees,
            'get_header_info': self._get_header_info(data['form']['fiscal_year_id']),
        }
