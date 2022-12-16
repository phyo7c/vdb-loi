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
        self.env.cr.execute("""select date_part('year',date_from)::text start_year,
                            date_part('year',date_to)::text end_year,
                            TO_CHAR(TO_DATE (date_part('month',date_from)::text, 'MM'), 'Month') AS start_month,
                            TO_CHAR(TO_DATE (date_part('month',date_to)::text, 'MM'), 'Month') AS end_month
                            from account_fiscal_year
                            where id=%s;""", (fiscal_year_id[0],))
        record = self.env.cr.fetchall()
        if record:
            start_year = record[0][0]
            end_year = record[0][1]
            start_month = record[0][2]
            end_month = record[0][3]
        return {
            'fiscal_year': fiscal_year_id[1],
            'fiscal_year_id': fiscal_year_id[0],
            'start_year': start_year,
            'end_year': end_year,
            'start_month': start_month,
            'end_month': end_month,
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        # if not data.get('form'):
        #     raise UserError(_("Form content is missing, this report cannot be printed."))

        income_tax_report = self.env['ir.actions.report']._get_report_from_name('income_tax_report.report_income_tax')
        employees = self.env['hr.employee'].browse(data['form']['emp'])
        fiscal_year_name = self.env['account.fiscal.year'].browse(data['form']['fiscal_year_id']).name
        fiscal_year = [data['form']['fiscal_year_id'], fiscal_year_name]
        return {
            'doc_ids': self.ids,
            'doc_model': income_tax_report.model,
            'docs': employees,
            'get_header_info': self._get_header_info(fiscal_year),
        }
