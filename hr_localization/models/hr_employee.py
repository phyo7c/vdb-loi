from odoo import fields, models, api, _
from odoo.osv import expression
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import date_utils
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
from odoo.tools.misc import format_date
import math


def time_to_float(value):
    return value.hour + value.minute / 60 + value.second / 3600


# class HrPayslipInput(models.Model):
#     _inherit = 'hr.payslip.input'
#
#     loan_line_ids = fields.Many2many('hr.loan.line', 'payslip_input_loan_line_rel', 'payslip_input_id', 'loan_line_id',
#                                      string="Loan Installment", help="Loan installment")
#     loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class Employee(models.Model):
    _inherit = 'hr.employee'

    ssb_not_calculate = fields.Boolean('SSB not calculate', default=False, copy=False)
    resign_date = fields.Date(string='Resign Date')
    salary_total = fields.Float(string='Previous Income Total')
    tax_paid = fields.Float(string='Previous Tax Paid')
    joining_date = fields.Date(string='Joining Date',
                               help="Employee joining date computed from the contract start date", store=True)
    father_exemption = fields.Boolean(string='Tax Exemption for Father')
    mother_exemption = fields.Boolean(string='Tax Exemption for Mother')
    father_name = fields.Char(string='Father Name')
    mother_name = fields.Char(string='Mother Name')
    spouse_exemption = fields.Boolean(string='Tax Exemption for Spouse')
    branch_id = fields.Many2one('res.branch', string='Branch',
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    name_in_mm = fields.Char('Name (in Myanmar)')
    financial_year = fields.Many2one('account.fiscal.year', string='Financial Year')
    over_60_ssb = fields.Boolean('Over 60 SSB', default=False, copy=False)
    over_60_ssb_percent = fields.Float('Over 60 SSB Percent')
    ssb_no = fields.Char('SSB No')
    ssb_issue_date = fields.Date('SSB Card Issue Date')
    ssb_temporary_card = fields.Selection([
        ('yes', "Yes"), ('no', "No")], default=False, string='Temporary Card (yes/no)')
    ssb_temporary_card_no = fields.Char('Temporary Card Number')
    smart_card = fields.Selection([
        ('yes', "Yes"), ('no', "No")], default=False, string='Smart Card (yes/no)')
    smart_card_issue_date = fields.Date('Smart Card Issue Date')
    smart_card_no = fields.Char('Smart Card Number')
    fingerprint_id = fields.Char(string='Fingerprint ID', default=lambda self: self._get_fingerprint_id())
    if_exclude = fields.Boolean('Exclude Fingerpirnt ID', default=False, copy=False)
    no_need_attendance = fields.Boolean('Payroll Calculate based on Leave', default=False, copy=False)
    permanent_date = fields.Date(string='Permanent Date')
    state = fields.Selection(
        [('probation', 'Probation'), ('extend_probation', 'Extended Probation'), ('permanent', 'Permanent')], 'State',
        default='probation')
    allow_leave_request = fields.Boolean('Leave Request', default=True, copy=False)
    allow_leave_report = fields.Boolean('Leave Report', default=True, copy=False)
    allow_attendance_report = fields.Boolean('Attendance Report', default=True, copy=False)
    allow_organization_chart = fields.Boolean('Organization Chart', default=True, copy=False)
    allow_pms = fields.Boolean('PMS', default=True, copy=False)
    allow_payslip = fields.Boolean('Payslip', default=True, copy=False)
    allow_overtime = fields.Boolean('Overtime', default=True, copy=False)
    allow_approval = fields.Boolean('Approval', default=True, copy=False)
    mobile_app_attendance = fields.Boolean('Mobile App Attendance', default=False, copy=False)
    approve_manager = fields.Many2one('hr.employee', string='Approve Manager', check_company=False,track_visibility='always')
    service_years = fields.Char('Service Years', compute='_compute_service_years', store=True)
    confirmation_date = fields.Date('Confirmation Date')
    age = fields.Char('Age', compute='_compute_age')

    @api.depends('birthday')
    def _compute_age(self):
        for emp in self:
            today = fields.Date.from_string(fields.Date.today())
            birthday = fields.Date.from_string(emp.birthday)
            duration = relativedelta(today, birthday)
            years = duration.years
            months = duration.months
            days = duration.days
            service_year = '{} years {} months {} days'.format(years, months, days)
            emp.age = service_year

    @api.depends('joining_date')
    def _compute_service_years(self):
        for emp in self:
            today = fields.Date.from_string(fields.Date.today())
            join_date = fields.Date.from_string(emp.joining_date)
            duration = relativedelta(today, join_date)
            years = duration.years
            months = duration.months
            days = duration.days
            service_year = '{} years {} months {} days'.format(years, months, days)
            emp.service_years = service_year

    def _get_fingerprint_id(self):
        self.env.cr.execute("""
            select max(fingerprint_id::int)+1
            from hr_employee
            where fingerprint_id is not null and active is True
            group by fingerprint_id
            order by fingerprint_id::int desc
            limit 1 
        """)
        code = self.env.cr.fetchone()
        if code:
            return code[0]

    def button_generate_code(self):
        self.env.cr.execute("""
            select max(fingerprint_id::int)+1
            from hr_employee
            where fingerprint_id is not null and active is True
            group by fingerprint_id
            order by fingerprint_id::int desc
            limit 1 
        """)
        code = self.env.cr.fetchone()
        if code:
            print("code : ", code[0])
            self.write({
                    "fingerprint_id": code[0],
                    "pin": code[0],
                    "barcode": code[0]
                })


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    previous_income = fields.Float('Previous Income', compute='_compute_previous_amount', store=True)
    previous_tax_paid = fields.Float('Previous Tax Paid', compute='_compute_previous_amount', store=True)
    remaining_months = fields.Integer('Remaining Months', compute='_compute_previous_amount', store=True)
    total_months = fields.Integer('Total Months', compute='_compute_previous_amount', store=True)
    sunday_unpaid = fields.Integer('Sunday Unpaid', compute='_compute_previous_amount', store=False)
    half_month_day = fields.Integer('Half Month Join', compute='_compute_previous_amount', store=False)
#
#     @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
#     def _onchange_employee(self):
#         if (not self.employee_id) or (not self.date_from) or (not self.date_to):
#             return
#
#         fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', self.date_to),
#                                                               ('date_to', '>=', self.date_to)])
#         if not fiscal_year:
#             action = self.env.ref('account.actions_account_fiscal_year')
#             raise RedirectWarning(_('You should configure a Fiscal Year first.'), action.id, _('Fiscal Years'))
#
#         employee = self.employee_id
#         date_from = self.date_from
#         date_to = self.date_to
#
#         print("employee : ", employee.id)
#         self.company_id = employee.company_id
#         if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
#             contracts = employee._get_contracts(date_from, date_to)
#             print("no contracts")
#             if not contracts:
#                 self.contract_id = False
#                 self.struct_id = False
#                 return
#             self.contract_id = contracts[0]
#             self.struct_id = contracts[0].struct_id or contracts[0].structure_type_id.default_struct_id
#
#         payslip_name = self.struct_id.payslip_name or _('Salary Slip')
#         self.name = '%s - %s - %s' % (
#             payslip_name, self.employee_id.name or '', format_date(self.env, self.date_from, date_format="MMMM y"))

        # if date_to > date_utils.end_of(fields.Date.today(), 'month'):
        #     self.warning_message = _(
        #         "This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
        #         (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        # else:
        #     self.warning_message = False

    #     self.worked_days_line_ids = self._get_new_worked_days_lines()
    #     self.input_line_ids = self._get_new_input_lines()
    #
    # def _get_input_lines(self):
    #     res = []
    #     self.ensure_one()
    #     struct = self.struct_id
    #     employee = self.employee_id
    #     date_from = self.date_from
    #     date_to = self.date_to
    #     calendar = self.employee_id.resource_calendar_id
    #     tz = timezone(calendar.tz)
    #     carloan_amount = shareloan_amount = eduloan_amt = 0
    #     commission_amount = 0
    #     input_type_obj = self.env['hr.payslip.input.type']
    #     other_allowance_input = self.env.ref('hr_localization.input_type_site_allowance')
        # other_deduction_input = self.env.ref('hr_localization.input_type_other_deduction')
        # logistics_commission_input = self.env.ref('hr_localization.input_type_sales_commission')
        # tmp_duty_ids = []
        # # DEDUCTION
        # deduction = self.env['hr.deduction'].sudo().search([('employee_id', '=', employee.id),
        #                                                     ('effective_date', '<=', date_to), '|',
        #                                                     ('end_date', '=', False),
        #                                                     ('end_date', '>=', date_to)])
        # if deduction:
        #     for ded in deduction:
        #         if ded.effective_type == 'one_time' and (ded.effective_date.month != date_from.month or ded.effective_date.year != date_from.year):
        #             continue
        #         elif ded.effective_type == 'yearly' and ded.effective_date.month != date_from.month:
        #             continue
        #         if ded.deduction_config_id.code in ('D01', 'D02'):
        #             input_type = input_type_obj.search([('code', '=', ded.deduction_config_id.code)])
        #             if input_type:
        #                 existing_ded = next((input for input in res if input["input_type_id"] == input_type.id), False)
        #                 if existing_ded:
        #                     existing_ded.update({'amount': existing_ded['amount'] + ded.amount})
        #                 else:
        #                     res.append({'input_type_id': input_type.id,
        #                                 'amount': ded.amount})
        #         else:
        #             res.append({'input_type_id': other_deduction_input.id,
        #                        'amount': ded.amount})

        # ALLOWANCE
        # allowance = self.env['hr.allowance'].sudo().search([('employee_id', '=', employee.id),
        #                                                     ('effective_date', '<=', date_to), '|',
        #                                                     ('end_date', '=', False),
        #                                                     ('end_date', '>=', date_to)])
        #
        # if allowance:
        #     for alw in allowance:
        #         if alw.effective_type == 'one_time' and (
        #                 alw.effective_date.month != date_from.month or alw.effective_date.year != date_from.year):
        #             continue
        #         elif alw.effective_type == 'yearly' and alw.effective_date.month != date_from.month:
        #             continue
        #         if alw.allowance_config_id.code in ('SA', 'SOA', 'BO', 'RBO', 'CSA', 'RLC', 'CA', 'TA', 'PHP', 'SSC'):
        #             input_type = input_type_obj.search([('code', '=', alw.allowance_config_id.code)])
        #             if input_type:
        #                 existing_alw = next((input for input in res if input["input_type_id"] == input_type.id), False)
        #                 if existing_alw:
        #                     existing_alw.update({'amount': existing_alw['amount'] + alw.amount})
        #                 else:
        #                     res.append({'input_type_id': input_type.id,
        #                                 'amount': alw.amount})
        #         else:
        #             res.append({'input_type_id': other_allowance_input.id,
        #                         'amount': alw.amount})

        # LOGISTICS COMMISSION
        # logistics_commission = self.env['hr.logistics.commission'].sudo().search([('employee_id', '=', employee.id),
        #                                                         ('from_datetime', '>=', str(date_from) + ' 00:00:00'),
        #                                                         ('from_datetime', '<=', str(date_from) + ' 23:59:59'),
        #                                                         ('to_datetime', '>=', str(date_to) + ' 00:00:00'),
        #                                                         ('to_datetime', '<=', str(date_to) + ' 23:59:59')])

        # if logistics_commission:
        #     for rec in logistics_commission:
        #         commission_amount += rec.commission
        #     if commission_amount:
        #         res.append({'input_type_id': logistics_commission_input.id,
        #                     'amount': commission_amount})

        # LOAN
        # import pdb
        # pdb.set_trace()
        # loan_line_obj = self.env['hr.loan.line'].sudo()
        # loans = loan_line_obj.search([('employee_id', '=', employee.id),
        #                               ('date', '>=', date_from),
        #                               ('date', '<=', date_to),
        #                               ('paid', '=', False),
        #                               ('loan_id.state', 'in', ('verify', 'approve'))])
        #
        # carloan_ids = shareloan_ids = eduloan_ids = loan_line_obj
        # print("eloan_ids>>>>",eloan_ids)
        # for loan in loans:
        #     if loan.loan_id.type == 'car':
        #         carloan_amount += loan.amount
        #         carloan_ids += loan
        #     elif loan.loan_id.type == 'share':
        #         shareloan_amount += loan.amount
        #         shareloan_ids += loan
        #     elif loan.loan_id.type == 'education':
        #         eduloan_amt += loan.amount
        #         eduloan_ids += loan
        #
        # if carloan_amount:
        #     print("Eloan " + str(carloan_ids))
        #     print("Eloan ids " + str(carloan_ids.ids))
        #     res.append({'input_type_id': self.env.ref('hr_localization.input_type_special_car_loan').id,
        #
        #                 'amount': carloan_amount})
        # if shareloan_amount:
        #     print("Tloan " + str(shareloan_ids))
        #     print("Tloan ids " + str(shareloan_ids.ids))
        #     res.append({'input_type_id': self.env.ref('hr_localization.input_type_share_loan').id,
        #
        #                 'amount': shareloan_amount})
        #
        # if eduloan_amt:
        #     print("Tloan " + str(eduloan_ids))
        #     print("Tloan ids " + str(eduloan_ids.ids))
        #     res.append({'input_type_id': self.env.ref('hr_localization.input_type_education_loan').id,
        #
        #                 'amount': eduloan_amt})

        # INSURANCE
        # insurance_line_obj = self.env['hr.insurance.line'].sudo()
        # insurance = insurance_line_obj.search([('employee_id', '=', employee.id),
        #                               ('date', '>=', date_from),
        #                               ('date', '<=', date_to),
        #                               ('paid', '!=', True)])
        # insurance_ids = insurance_line_obj.browse([])
        # insurance_amount = 0.0
        # for i in insurance:
        #     insurance_amount += i.amount
        #     insurance_ids += i
        # if insurance_amount:
        #     res.append({'input_type_id': self.env.ref('hr_localization.other_input_type_insurance_deduction').id,
        #                 'insurance_line_ids': [(6, 0, insurance_ids.ids)],
        #                 'amount': insurance_amount})

        # OT
        # duty_structs = self.env['hr.payroll.structure'].search([('name', 'in', ('ST05', 'ST06', 'ST07', 'ST08'))])
        #         duty_structs = self.env['hr.payroll.structure'].search([('shift', '=', True)])
        #         daily_struct = self.env.ref('hr_localization.structure_daily_wages')

        #         ot_duty = late = 0
        #         start_time = (tz.localize(datetime(year=date_from.year, month=date_from.month, day=date_from.day), is_dst=None)).astimezone(UTC)
        #         end_time = (tz.localize(datetime(year=date_to.year, month=date_to.month, day=date_to.day), is_dst=None)).astimezone(UTC) + timedelta(days=1)

        #         attendances = self.env['hr.attendance'].search([('employee_id', '=', employee.id),
        #                                                         ('check_in', '>=', start_time),
        #                                                         ('check_in', '<', end_time),('no_worked_day', '=',False),
        #                                                         ('is_absent','=',False),('missed','=',False),('leave','=',False),
        #                                                         ('state', 'in', ('approve', 'verify'))], order='check_in asc')
        #         for att in attendances:
        #             if att.id in [119695]:#[153485,153486,153501,153502,153504,153488,153489]:
        #                 print("test",att.id)
        #             check_in = att.check_in.astimezone(tz)
        #             check_out = att.check_out and att.check_out.astimezone(tz) or False
        #             begin_date = att.check_in + timedelta(hours=+6,minutes=+30)
        #             print("begin_date.date()>>>",check_in.date())
        #             dayofweek = begin_date.weekday()
        #             oneday_off = False
        #             public_holiday = self.env['public.holidays.line'].search([('date', '=', begin_date.date()),
        #                                                                       ('line_id.company_id', '=', att.employee_id.company_id.id)], order='id desc', limit=1)

        #             if not public_holiday:
        #                 public_holiday = self.env['public.holidays.line'].search([('date', '=', begin_date.date()),
        #                                                                           ('line_id.company_id', '=', False)], order='id desc', limit=1)

        #             working_hours = self._get_work_hours(begin_date.date(), calendar, dayofweek)
        #             #add logic special calculation for ot duty on one day off and no holiday shift
        #             if not public_holiday:
        # #                 if (self.employee_id.resource_calendar_id.one_day_off == True and dayofweek==6):
        # #                     dayofweek = 1 #change one day off disable as all one day off will closed sunday
        #                 if self.employee_id.resource_calendar_id.one_day_off == True and not working_hours:
        #                     oneday_off = True
        #                     continue
        #                 elif self.employee_id.resource_calendar_id.no_holidays == True and dayofweek==6:
        #                     continue
        #             if (self.employee_id.resource_calendar_id.one_day_off == True and self.employee_id.resource_calendar_id.hours_per_day > 11) or (self.employee_id.resource_calendar_id.no_holidays == True and self.employee_id.resource_calendar_id.hours_per_day > 11):
        #                 if not ((public_holiday and public_holiday.type == 'holiday') or (not public_holiday and dayofweek == 6)):
        #                     if struct in duty_structs:
        #                         dayofweek = begin_date.weekday()
        #                         work_hours = self._get_work_hours(begin_date.date(), calendar, dayofweek)
        #                         if work_hours:
        #                             if len(work_hours) == 1:
        #                                 work_hour = work_hours.hour_to - work_hours.hour_from
        #                                 take_leave = self.check_leave(self.employee_id, begin_date.date(), work_hours.hour_from, work_hours.hour_to)
        #                                 if work_hour > 8 and check_in and check_out:
        #                                     ot_duty += (work_hour - 8) / take_leave
        #                                     tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':work_hour - 8})
        #                                 elif work_hour > 4 and check_in and check_out:
        #                                     ot_duty += (work_hour - 4) / take_leave
        #                                     tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':work_hour - 4})
        #                             elif len(work_hours) == 2:
        #                                 work_hour = 0
        #                                 for wh in work_hours:
        #                                     work_hour += wh.hour_to - wh.hour_from
        #                                 if work_hour > 8 and check_in and check_out:
        #                                     ot_duty += 2

        #                                 tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':2})
        #                     elif struct == daily_struct:
        #                         late += math.ceil(att.late_minutes)
        #                 continue
        # end ot duty logic

        # public_holiday = self.env['public.holidays.line'].search([('date', '=', begin_date.date())])
        #     print("check_in.date()>>>",check_in.date())
        #     print("att.check_in>>>",att.check_in)
        #     print("att.check_in>>>",att.check_in.date())
        #     if not ((public_holiday and public_holiday.type == 'holiday') or (not public_holiday and dayofweek == 6 )):
        #         if struct in duty_structs:
        #             dayofweek = begin_date.weekday()
        #             work_hours = self._get_work_hours(check_in, calendar, dayofweek)
        #             if work_hours:
        #                 if check_out and round(time_to_float(check_out)) == 24:
        #                     start_work_hour = work_hours.filtered(lambda wh: round(wh.hour_to) == 24)
        #                     next_day = check_in + timedelta(days=1)
        #                     next_work_hours = self._get_work_hours(next_day, calendar, next_day.weekday())
        #                     end_work_hour = next_work_hours.filtered(lambda wh: round(wh.hour_from) == 0)
        #                     next_start = (tz.localize(datetime(year=next_day.year, month=next_day.month, day=next_day.day), is_dst=None)).astimezone(UTC)
        #                     next_end = next_start + timedelta(days=1, seconds=-1)
        #                     next_attend = self.env['hr.attendance'].search([('employee_id', '=', employee.id),
        #                                                                     ('check_in', '>=', next_start),
        #                                                                     ('check_in', '<', next_end),
        #                                                                     ('state', 'in', ('approve', 'verify'))],
        #                                                                    order='check_in asc', limit=1)

        #                     if start_work_hour and end_work_hour and next_attend:
        #                         work_hour = (24 + end_work_hour.hour_to) - start_work_hour.hour_from
        #                         print("work_hour>>",round(time_to_float(next_attend.check_in.astimezone(tz))))
        #                         print("work_hour>>",next_attend.check_in.astimezone(tz))
        #                         if work_hour > 8 and round(time_to_float(next_attend.check_in.astimezone(tz))) == 0:
        #                             ot_duty += work_hour - 8
        #                             tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':work_hour - 8})
        #                         elif work_hour > 4:
        #                             ot_duty += work_hour - 4
        #                             tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':work_hour - 4})
        #                 elif round(time_to_float(check_in)) == 0:
        #                     pass
        #                 else:
        #                     if len(work_hours) == 1:
        #                         work_hour = work_hours.hour_to - work_hours.hour_from
        #                         if work_hour > 8 and check_out:
        #                             ot_duty += work_hour - 8
        #                             tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':work_hour - 8})
        #                         elif (work_hour/2) > 4 and check_out:
        #                             ot_duty += work_hour - 4
        #                             tmp_duty_ids.append({'id':att.id,'time':begin_date.date(),'hour':work_hour - 4})
        #             else:
        #                 average_hours_per_day = round(calendar.hours_per_day)
        #                 ot_duty += average_hours_per_day - 8

        #         elif struct == daily_struct:
        #             late += math.ceil(att.late_minutes)

        # if ot_duty:
        #     print("tmp_duty_ids>>",tmp_duty_ids)
        #     res.append({'input_type_id': self.env.ref('hr_localization.other_input_type_ot_duty').id,
        #                 'amount': ot_duty})
        # if late:
        #     res.append({'input_type_id': self.env.ref('hr_localization.other_input_type_late').id,
        #                 'amount': late})
    #     return res
    #
    # def _get_new_input_lines(self):
    #     input_line_values = self._get_input_lines()
    #     input_lines = self.input_line_ids.browse([])
    #     for r in input_line_values:
    #         input_lines |= input_lines.new(r)
    #     return input_lines
    #
    def _get_sunday_list(self, employee_id, date_from, date_to):
        end_date = date_to
        beg_date = date_from
        sunday_list = []
        sunday_count = 0
        while beg_date <= end_date:
            dayofweek = beg_date.weekday()
            if dayofweek == 6:
                saturday = beg_date + timedelta(days=-1)
                monday = beg_date + timedelta(days=1)
                res = {'Saturday': saturday.strftime("%Y-%m-%d "), 'Sunday': beg_date.strftime("%Y-%m-%d "),
                       'Monday': monday.strftime("%Y-%m-%d ")}
                sunday_list.append(res)
            beg_date = beg_date + timedelta(days=1)
    
        for sunday in sunday_list:
            sunday_flg = False
            sunday_leave = self.env['hr.leave'].search(
                [('request_date_from', '=', sunday['Saturday']), ('holiday_status_id', '=', 4),
                 ('state', 'in', ['validate', 'validate1']),
                 ('employee_id', '=', employee_id.id)], limit=1)
            monday_leave = self.env['hr.leave'].search(
                [('request_date_to', '=', sunday['Monday']), ('holiday_status_id', '=', 4),
                 ('state', 'in', ['validate', 'validate1']),
                 ('employee_id', '=', employee_id.id)], limit=1)
            if sunday_leave and monday_leave:
                # if employee_id.resource_calendar_id.no_holidays == True:
                sunday_count += 1
                sunday_flg = True
    
            # if not sunday_leave or not monday_leave:
            #     gz_count = self._get_gz_holiday_leave(employee_id, sunday['Saturday'], sunday['Monday'], date_from,
            #                                           date_to)
            #     print("gz_count>>>>>>", gz_count)
            #     if gz_count > 0:
            #         sunday_count += gz_count  # + 1
            #         sunday_flg = True
            #         continue
            if sunday_flg == True:
                continue
            leave = self.env['hr.leave'].search(
                [('request_date_from', '<=', sunday['Saturday']), ('request_date_to', '>=', sunday['Monday']),
                 ('holiday_status_id', '=', 4), ('state', 'in', ['validate', 'validate1']),
                 ('employee_id', '=', employee_id.id)], limit=1)
            if leave:
                sunday_count += 1
        return sunday_count
    #
    # def _get_gz_holiday_leave(self, employee_id, beg_date, end_date, date_from, date_to):
    #     holiday_count = 0
    #     before_holiday_count = 0
    #     after_holiday_count = 0
    #     holiday_list = []
    #     beg_saturday = datetime.strptime(beg_date + '00:00:00', '%Y-%m-%d %H:%M:%S').date()
    #     end_monday = datetime.strptime(end_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S').date()
    #     beg_holiday = datetime.strptime(beg_date + '00:00:00', '%Y-%m-%d %H:%M:%S').date()  # + timedelta(days=-1)
    #     end_holiday = datetime.strptime(end_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S').date()  # + timedelta(days=1)
    #     before_saturday = after_sunday = False
    #     before = after = 1
    #     while before != 0:
    #         public_holiday = self.env['public.holidays.line'].search([('date', '=', beg_holiday),
    #                                                                   ('line_id.company_id', '=',
    #                                                                    employee_id.company_id.id)], order='id desc',
    #                                                                  limit=1)
    #
    #         if not public_holiday:
    #             public_holiday = self.env['public.holidays.line'].search([('date', '=', beg_holiday),
    #                                                                       ('line_id.company_id', '=', False)],
    #                                                                      order='id desc', limit=1)
    #         if public_holiday:
    #             holiday_list.append(public_holiday.date)
    #             beg_holiday = beg_holiday + timedelta(days=-1)
    #             before_holiday_count += 1
    #         else:
    #             leave = self.env['hr.leave'].search(
    #                 [('request_date_from', '=', beg_holiday), ('holiday_status_id', '=', 4),
    #                  ('state', 'in', ['validate', 'validate1']),
    #                  ('employee_id', '=', employee_id.id)], limit=1)
    #             print(str(beg_holiday))
    #             if leave:
    #                 if beg_holiday != beg_saturday:
    #                     before_saturday = True
    #                     # before_holiday_count +=1
    #                     beg_holiday = beg_holiday + timedelta(days=-1)
    #                     before = 0
    #
    #                 else:
    #                     before = 0
    #             else:
    #                 before = 0
    #             if before_saturday == True:
    #                 holiday_count = before_holiday_count
    #     while after != 0:
    #         public_holiday = self.env['public.holidays.line'].search([('date', '=', end_holiday),
    #                                                                   ('line_id.company_id', '=',
    #                                                                    employee_id.company_id.id)], order='id desc',
    #                                                                  limit=1)
    #
    #         if not public_holiday:
    #             public_holiday = self.env['public.holidays.line'].search([('date', '=', end_holiday),
    #                                                                       ('line_id.company_id', '=', False)],
    #                                                                      order='id desc', limit=1)
    #         if public_holiday:
    #             holiday_list.append(public_holiday.date)
    #             end_holiday = end_holiday + timedelta(days=1)
    #             after_holiday_count += 1
    #         else:
    #             leave = self.env['hr.leave'].search(
    #                 [('request_date_from', '=', end_holiday), ('holiday_status_id', '=', 4),
    #                  ('state', 'in', ['validate', 'validate1']),
    #                  ('employee_id', '=', employee_id.id)], limit=1)
    #             if leave:
    #                 if end_holiday != end_monday:
    #                     after_sunday = True
    #                     # after_holiday_count +=1
    #                     end_holiday = end_holiday + timedelta(days=1)
    #                     after = 0
    #                 else:
    #                     after = 0
    #             else:
    #                 after = 0
    #             if after_sunday == True:
    #                 holiday_count += after_holiday_count + 1
    #
    #     leave_start = self.env['hr.leave'].search([('request_date_from', '=', date_from), ('holiday_status_id', '=', 4),
    #                                                ('state', 'in', ['validate', 'validate1']),
    #                                                ('employee_id', '=', employee_id.id)], limit=1)
    #     leave_end = self.env['hr.leave'].search([('request_date_from', '=', date_to), ('holiday_status_id', '=', 4),
    #                                              ('state', 'in', ['validate', 'validate1']),
    #                                              ('employee_id', '=', employee_id.id)], limit=1)
    #     if leave_start and leave_end:
    #         public_holidays = self.env['public.holidays.line'].search(
    #             [('date', '>=', date_from), ('date', '<=', date_to),
    #              ('line_id.company_id', '=', employee_id.company_id.id)], order='id desc')
    #         if not public_holidays:
    #             public_holidays = self.env['public.holidays.line'].search(
    #                 [('date', '>=', date_from), ('date', '<=', date_to),
    #                  ('line_id.company_id', '=', False)], order='id desc')
    #         for holiday in public_holidays:
    #             if holiday.date not in holiday_list:
    #                 dayofweek = holiday.date.weekday()
    #                 print(dayofweek)
    #                 if dayofweek != 6 and dayofweek != 5 and dayofweek != 0:
    #                     holiday_list.append(holiday.date)
    #                     holiday_count += 1
    #     return holiday_count
    #
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_previous_amount(self):
        for slip in self:
            prev_income = slip.employee_id.salary_total
            prev_tax_paid = slip.employee_id.tax_paid
            remaining_months = 0
            total_months = 12
            today = fields.Date.today()
            fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', slip.date_to),
                                                                  ('date_to', '>=', slip.date_to),
                                                                  ('company_id', '=', slip.employee_id.company_id.id)])
            print("_compute_previous_amount>>>", fiscal_year, slip.date_to)
            if fiscal_year:
                remaining_months = relativedelta(fiscal_year.date_to, slip.date_to).months
                if slip.employee_id.joining_date and slip.employee_id.joining_date > fiscal_year.date_from:
                    total_months = 12 - relativedelta(slip.employee_id.joining_date, fiscal_year.date_from).months
                payslips = self.env['hr.payslip'].search([('employee_id', '=', slip.employee_id.id),
                                                          ('date_to', '>=', fiscal_year.date_from),
                                                          ('date_to', '<=', fiscal_year.date_to),
                                                          ('state', 'not in', ('draft', 'cancel'))])
                for pay in payslips:
                    slipline_obj = self.env['hr.payslip.line']
                    basic = slipline_obj.search([('slip_id', '=', pay.id), ('code', '=', 'BASIC')])
                    # deductions = slipline_obj.search([('slip_id', '=', pay.id), ('code', 'in', ('UNPAID', 'SSB'))])
                    deductions = slipline_obj.search([('slip_id', '=', pay.id), ('code', '=', 'D03')])
                    tax_paid = slipline_obj.search([('slip_id', '=', pay.id), ('code', '=', 'ICT')])
                    prev_income += basic and basic.total or 0
                    prev_income -= sum([abs(ded.total) for ded in deductions])
                    prev_tax_paid += tax_paid and tax_paid.total or 0
    
            sunday_unpaid = self._get_sunday_list(slip.employee_id, slip.date_from, slip.date_to)
            slip.remaining_months = remaining_months
            slip.previous_income = prev_income
            slip.previous_tax_paid = prev_tax_paid
            slip.total_months = total_months
            slip.sunday_unpaid = sunday_unpaid
            slip.half_month_day = 0
            if slip.employee_id.joining_date and (
                    datetime.strptime(str(slip.employee_id.joining_date), '%Y-%m-%d').strftime(
                            "%Y-%m") == datetime.strptime(str(slip.date_from), '%Y-%m-%d').strftime("%Y-%m")):
                delta = slip.date_to - slip.employee_id.joining_date
                slip.half_month_day = delta.days + 1
            elif slip.employee_id.resign_date and (
                    datetime.strptime(str(slip.employee_id.resign_date), '%Y-%m-%d').strftime(
                            "%Y-%m") == datetime.strptime(str(slip.date_from), '%Y-%m-%d').strftime("%Y-%m")):
                delta = slip.date_to - slip.employee_id.resign_date
                slip.half_month_day = delta.days + 1
            # if slip.employee_id and slip.date_from:
            #     current_fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', today),
            #                                                                   ('date_to', '>=', today),
            #                                                                   ('company_id', '=',
            #                                                                    slip.employee_id.company_id.id)])
            #     if slip.date_from >= current_fiscal_year.date_from and slip.date_from <= current_fiscal_year.date_to:
            #         slip.previous_income = 0
            #         slip.previous_tax_paid = 0
            print("sunday_unpaid>>>", sunday_unpaid)
    #
    # def calculate_taken_anaual_leave(self):
    #     # import pdb
    #     # pdb.set_trace()
    #
    #     allocation_id = self.env['hr.leave.allocation'].search([('private_name', '=', 'Anaual Leave Previous')]).id
    #     leave = 0
    #     taken_leave = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('request_date_from', '>', self.date_from),
    #          ('request_date_to', '>', self.date_from), ('request_date_from', '<', self.date_to),
    #          ('request_date_to', '<', self.date_to), ('holiday_allocation_id', '=', allocation_id)])
    #
    #     for taken in taken_leave:
    #         leave += taken.number_of_days
    #
    #     return leave
    #
    # def calculate_taken_anaual_leave_current(self):
    #     # import pdb
    #     # pdb.set_trace()
    #
    #     allocation_id = self.env['hr.leave.allocation'].search([('private_name', '=', 'Anaual Leave Current')]).id
    #     leave = 0
    #     taken_leave = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('request_date_from', '>', self.date_from),
    #          ('request_date_to', '>', self.date_from), ('request_date_from', '<', self.date_to),
    #          ('request_date_to', '<', self.date_to), ('holiday_allocation_id', '=', allocation_id)])
    #
    #     for taken in taken_leave:
    #         leave += taken.number_of_days
    #
    #     return leave
    #
    # def calculate_taken_recuperation(self):
    #     # import pdb
    #     # pdb.set_trace()
    #
    #     allocation_id = self.env['hr.leave.allocation'].search([('private_name', '=', 'Recuperation Days')]).id
    #     leave = 0
    #     taken_leave = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('request_date_from', '>', self.date_from),
    #          ('request_date_to', '>', self.date_from), ('request_date_from', '<', self.date_to),
    #          ('request_date_to', '<', self.date_to), ('holiday_allocation_id', '=', allocation_id)])
    #
    #     for taken in taken_leave:
    #         leave += taken.number_of_days
    #
    #     return leave
    #
    # def calculate_taken_casual(self):
    #     # import pdb
    #     # pdb.set_trace()
    #
    #     allocation_id = self.env['hr.leave.allocation'].search([('private_name', '=', 'Casual Days')]).id
    #     leave = 0
    #     taken_leave = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('request_date_from', '>', self.date_from),
    #          ('request_date_to', '>', self.date_from), ('request_date_from', '<', self.date_to),
    #          ('request_date_to', '<', self.date_to), ('holiday_allocation_id', '=', allocation_id)])
    #
    #     for taken in taken_leave:
    #         leave += taken.number_of_days
    #
    #     return leave
    #
    # def calculate_taken_ext_work(self):
    #     # import pdb
    #     # pdb.set_trace()
    #
    #     allocation_id = self.env['hr.leave.allocation'].search([('private_name', '=', 'Ext Work Hours')]).id
    #     leave = 0
    #     taken_leave = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('request_date_from', '>', self.date_from),
    #          ('request_date_to', '>', self.date_from), ('request_date_from', '<', self.date_to),
    #          ('request_date_to', '<', self.date_to), ('holiday_allocation_id', '=', allocation_id)])
    #
    #     for taken in taken_leave:
    #         leave += taken.number_of_days
    #
    #     return leave
    #
    # def calculate_taken_short_recuperation(self):
    #     # import pdb
    #     # pdb.set_trace()
    #
    #     allocation_id = self.env['hr.leave.allocation'].search([('private_name', '=', 'Short Recuperation Days')]).id
    #     leave = 0
    #     taken_leave = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('request_date_from', '>', self.date_from),
    #          ('request_date_to', '>', self.date_from), ('request_date_from', '<', self.date_to),
    #          ('request_date_to', '<', self.date_to), ('holiday_allocation_id', '=', allocation_id)])
    #
    #     for taken in taken_leave:
    #         leave += taken.number_of_days
    #
    #     return leave
    #
    # def anaual_leave_previous(self):
    #     anaual_leave = 0
    #     previous = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id), ('private_name', '=', 'Anaual Leave Previous')])
    #     if previous:
    #         anaual_leave += previous.number_of_days
    #     return anaual_leave
    #
    # def anaual_leave_current(self):
    #     anaual_leave = 0
    #     current = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id), ('private_name', '=', 'Anaual Leave Current')])
    #     if current:
    #         anaual_leave += current.number_of_days
    #
    #     return anaual_leave
    #
    # def recuperation_days(self):
    #     recuperation_days = 0
    #     recuperation = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id), ('private_name', '=', 'Recuperation Days')])
    #     if recuperation:
    #         recuperation_days += recuperation.number_of_days
    #     return recuperation_days
    #
    # def casual_days(self):
    #     casual_days = 0
    #     casual = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id), ('private_name', '=', 'Casual Days')])
    #     if casual:
    #         casual_days += casual.number_of_days
    #     return casual_days
    #
    # def ext_work_hr(self):
    #     ext_work_hr = 0
    #     ext_work = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id), ('private_name', '=', 'Ext Work Hours')])
    #     if ext_work:
    #         ext_work_hr += ext_work.number_of_days
    #     return ext_work_hr
    #
    # def short_recuperation_days(self):
    #     short_recuperation_days = 0
    #     short_recuperation = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id), ('private_name', '=', 'Short Recuperation Days')])
    #     if short_recuperation:
    #         short_recuperation_days += short_recuperation.number_of_days
    #     return short_recuperation_days
    #
    # def gross_fiscal_year(self):
    #     # import pdb
    #     # pdb.set_trace()
    #     gross_amt = 0
    #     fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', self.date_to),
    #                                                           ('date_to', '>=', self.date_to)])
    #     payslip_ids = []
    #     if fiscal_year:
    #
    #         payslip_obj = self.env['hr.payslip']
    #
    #         payslip_ids = payslip_obj.search(
    #             [('date_to', '>=', fiscal_year.date_from), ('date_to', '<=', fiscal_year.date_to),
    #              ('employee_id', '=', self.employee_id.id)
    #                 , ('date_to', '<=', self.date_to)])
    #
    #         print("Hello", payslip_ids)
    #
    #         for payslip in payslip_ids:
    #             payslip_line_obj = self.env['hr.payslip.line']
    #             payslip_line = payslip_line_obj.search(
    #                 [('slip_id', '=', payslip.id), ('category_id.code', '=', 'GROSS')])
    #             if payslip_line:
    #                 gross_amt += payslip_line.amount
    #
    #     return gross_amt
    #
    # def net_fiscal_year(self):
    #     # import pdb
    #     # pdb.set_trace()
    #     net_amt = 0
    #     fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', self.date_to),
    #                                                           ('date_to', '>=', self.date_to)])
    #     payslip_ids = []
    #     if fiscal_year:
    #         #     action = self.env.ref('account.actions_account_fiscal_year')
    #         #     raise RedirectWarning(_('You should configure a Fiscal Year first.'), action.id, _('Fiscal Years'))
    #
    #         # else:
    #
    #         payslip_obj = self.env['hr.payslip']
    #
    #         payslip_ids = payslip_obj.search(
    #             [('date_to', '>=', fiscal_year.date_from), ('date_to', '<=', fiscal_year.date_to),
    #              ('employee_id', '=', self.employee_id.id)
    #                 , ('date_to', '<=', self.date_to)])
    #
    #         print("Hello", payslip_ids)
    #
    #         for payslip in payslip_ids:
    #             payslip_line_obj = self.env['hr.payslip.line']
    #             payslip_line = payslip_line_obj.search([('slip_id', '=', payslip.id), ('category_id.code', '=', 'NET')])
    #             if payslip_line:
    #                 net_amt += payslip_line.amount
    #
    #     return net_amt
    #
    # def income_tax_fiscal_year(self):
    #     # import pdb
    #     # pdb.set_trace()
    #     income_tax_amt = 0
    #     fiscal_year = self.env['account.fiscal.year'].search([('date_from', '<=', self.date_to),
    #                                                           ('date_to', '>=', self.date_to)])
    #     payslip_ids = []
    #     if fiscal_year:
    #         #     action = self.env.ref('account.actions_account_fiscal_year')
    #         #     raise RedirectWarning(_('You should configure a Fiscal Year first.'), action.id, _('Fiscal Years'))
    #
    #         # else:
    #
    #         payslip_obj = self.env['hr.payslip']
    #
    #         payslip_ids = payslip_obj.search(
    #             [('date_to', '>=', fiscal_year.date_from), ('date_to', '<=', fiscal_year.date_to),
    #              ('employee_id', '=', self.employee_id.id)
    #                 , ('date_to', '<=', self.date_to)])
    #
    #         print("Hello", payslip_ids)
    #
    #         for payslip in payslip_ids:
    #             payslip_line_obj = self.env['hr.payslip.line']
    #             payslip_line = payslip_line_obj.search(
    #                 [('slip_id', '=', payslip.id), ('salary_rule_id.code', '=', 'ICT')])
    #             if payslip_line:
    #                 income_tax_amt += payslip_line.amount
    #
    #     return income_tax_amt
    
class JobType(models.Model):
    _name = "hr.job.type"
    
    name = fields.Char(string="Job Type") 


class Job(models.Model):

    _inherit = "hr.job"
    
    
    job_type = fields.Many2one('hr.job.type',string="Job Type")
    daily_wages = fields.Boolean( string="Daily Wages" )

