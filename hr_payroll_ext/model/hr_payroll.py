import math
from odoo import api,Command, models, fields, _
from odoo.tools import date_utils
from odoo.tools.misc import format_date
from pytz import timezone, UTC
from collections import defaultdict

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from calendar import monthrange
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.tools import float_round, date_utils, convert_file, html2plaintext

from odoo.tools import float_compare, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import pytz

import calendar


from odoo.osv import expression


def float_to_hr_min(value):
    if value < 0:
        value = abs(value)

    hour = int(value)
    minute = round((value % 1) * 60)

    if minute == 60:
        minute = 0
        hour = hour + 1
    return hour, minute

def float_to_time(value):
    if value < 0:
        value = abs(value)

    hour = int(value)
    minute = round((value % 1) * 60)

    if minute == 60:
        minute = 0
        hour = hour + 1
    return time(hour, minute)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    is_sec_contract = fields.Boolean('Two Contract?')
    second_contract_id = fields.Many2one(
        'hr.contract', string='Second Contract', domain="[('company_id', '=', company_id)]",
        compute='_compute_contract_id', store=True, readonly=False,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'paid': [('readonly', True)]})
    days_of_month = fields.Float('Days of Month', compute='_compute_day_of_month',store=True)
    

    @api.depends('date_from','date_to')
    def _compute_day_of_month(self):
        for slip in self:
            
            if slip.date_from and slip.date_to:
            
                slip.days_of_month = monthrange(slip.date_from.year, slip.date_from.month)[1]

    def _get_worked_day_lines(self):
        self.ensure_one()
        res = super()._get_worked_day_lines()
        attendance_id = self.env.ref('hr_work_entry.work_entry_type_attendance').id
        out_of_contract_id = self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract').id
        for data in res:
            if data['work_entry_type_id'] in (attendance_id, out_of_contract_id):
                data['number_of_days'] = round(data['number_of_days'], 0)
        return res

    # def _get_payslip_lines(self):
    #     self.ensure_one()

    #     slip_days = self.date_to - self.date_from
    #     slip_days = slip_days.days + 1

    #     if self.second_contract_id:
    #         end_date = self.contract_id.date_end
    #         day = end_date - self.date_from
    #         day = day.days + 1
    #         if day:
    #             contract_limit = day / slip_days
    #     else:
    #         contract_limit = 1

    #     localdict = self.env.context.get('force_payslip_localdict', None)
    #     if localdict is None:
    #         localdict = self._get_localdict()

    #     rules_dict = localdict['rules'].dict
    #     result_rules_dict = localdict['result_rules'].dict

    #     blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

    #     result = {}

    #     for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
    #         if rule.id in blacklisted_rule_ids:
    #             continue
    #         localdict.update({
    #             'result': None,
    #             'result_qty': 1.0,
    #             'result_rate': 100,
    #             'result_name': False
    #         })
    #         if rule._satisfy_condition(localdict):
    #             amount, qty, rate = rule._compute_rule(localdict)
    #             #check if there is already a rule computed with that code
    #             previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
    #             #set/overwrite the amount computed for this rule in the localdict
    #             tot_rule = amount * qty * rate / 100.0
    #             localdict[rule.code] = tot_rule
    #             result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
    #             rules_dict[rule.code] = rule
    #             # sum the amount for its salary category
    #             localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
    #             # Retrieve the line name in the employee's lang
    #             employee_lang = self.employee_id.sudo().address_home_id.lang
    #             # This actually has an impact, don't remove this line
    #             context = {'lang': employee_lang}
    #             if localdict['result_name']:
    #                 rule_name = localdict['result_name']
    #             elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION', 'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
    #                 if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
    #                     if rule.name == "Double Holiday Pay":
    #                         rule_name = _("Double Holiday Pay")
    #                     if rule.struct_id.name == "CP200: Employees 13th Month":
    #                         rule_name = _("Prorated end-of-year bonus")
    #                     else:
    #                         rule_name = _('Basic Salary')
    #                 elif rule.code == "GROSS":
    #                     rule_name = _('Gross')
    #                 elif rule.code == "DEDUCTION":
    #                     rule_name = _('Deduction')
    #                 elif rule.code == "REIMBURSEMENT":
    #                     rule_name = _('Reimbursement')
    #                 elif rule.code == 'NET':
    #                     rule_name = _('Net Salary')
    #             else:
    #                 rule_name = rule.with_context(lang=employee_lang).name
    #             # create/overwrite the rule in the temporary results
    #             result[rule.code] = {
    #                 'sequence': rule.sequence,
    #                 'code': rule.code,
    #                 'name': rule_name,
    #                 'note': html2plaintext(rule.note),
    #                 'salary_rule_id': rule.id,
    #                 'contract_id': localdict['contract'].id,
    #                 'employee_id': localdict['employee'].id,
    #                 'amount': amount * contract_limit,
    #                 'quantity': qty,
    #                 'rate': rate,
    #                 'slip_id': self.id,
    #             }
    #     if self.second_contract_id:
    #         start_date = self.second_contract_id.date_start
    #         day = self.date_to - start_date
    #         day = day.days + 1
    #         if day:
    #             contract_limit = day / slip_days
    #         localdict['contract'] = self.second_contract_id
    #         rules_dict = localdict['rules'].dict
    #         result_rules_dict = localdict['result_rules'].dict

    #         blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

    #         result_dict = {}

    #         for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
    #             if rule.id in blacklisted_rule_ids:
    #                 continue
    #             localdict.update({
    #                 'result': None,
    #                 'result_qty': 1.0,
    #                 'result_rate': 100,
    #                 'result_name': False
    #             })
    #             if rule._satisfy_condition(localdict):
    #                 amount, qty, rate = rule._compute_rule(localdict)
    #                 # check if there is already a rule computed with that code
    #                 previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
    #                 # set/overwrite the amount computed for this rule in the localdict
    #                 tot_rule = amount * qty * rate / 100.0
    #                 localdict[rule.code] = tot_rule
    #                 result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
    #                 rules_dict[rule.code] = rule
    #                 # sum the amount for its salary category
    #                 localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
    #                 # Retrieve the line name in the employee's lang
    #                 employee_lang = self.employee_id.sudo().address_home_id.lang
    #                 # This actually has an impact, don't remove this line
    #                 context = {'lang': employee_lang}
    #                 if localdict['result_name']:
    #                     rule_name = localdict['result_name']
    #                 elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION',
    #                                    'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
    #                     if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
    #                         if rule.name == "Double Holiday Pay":
    #                             rule_name = _("Double Holiday Pay")
    #                         if rule.struct_id.name == "CP200: Employees 13th Month":
    #                             rule_name = _("Prorated end-of-year bonus")
    #                         else:
    #                             rule_name = _('Basic Salary')
    #                     elif rule.code == "GROSS":
    #                         rule_name = _('Gross')
    #                     elif rule.code == "DEDUCTION":
    #                         rule_name = _('Deduction')
    #                     elif rule.code == "REIMBURSEMENT":
    #                         rule_name = _('Reimbursement')
    #                     elif rule.code == 'NET':
    #                         rule_name = _('Net Salary')
    #                 else:
    #                     rule_name = rule.with_context(lang=employee_lang).name
    #                 # create/overwrite the rule in the temporary results
    #                 result_dict[rule.code] = {
    #                     'sequence': rule.sequence,
    #                     'code': rule.code,
    #                     'name': rule_name,
    #                     'note': html2plaintext(rule.note),
    #                     'salary_rule_id': rule.id,
    #                     'contract_id': localdict['contract'].id,
    #                     'employee_id': localdict['employee'].id,
    #                     'amount': amount * contract_limit,
    #                     'quantity': qty,
    #                     'rate': rate,
    #                     'slip_id': self.id,
    #                 }
    #         for rule in set(result_dict):
    #             for key in set(result_dict.get(rule, 0)):
    #                 if key == 'amount':
    #                     result[rule][key] = result_dict.get(rule, 0).get(key, 0) + result.get(rule, 0).get(key, 0)
    #     return result.values()

    # def _get_payslip_lines(self):
    #     self.ensure_one()
    #     localdict = self.env.context.get('force_payslip_localdict', None)
    #     if localdict is None:
    #         localdict = self._get_localdict()
    #
    #     from_date = self.date_from
    #     to_date = self.date_to
    #     slip_days = to_date - from_date
    #     slip_days = slip_days.days + 1
    #     copy_localdict = localdict.copy()
    #     result_dict = {}
    #     first_flag = True
    #     for contract in copy_localdict['contract']:
    #         start_date = contract.date_start
    #         end_date = contract.date_end
    #         if from_date < end_date and from_date > start_date:
    #             day = end_date - from_date
    #             day = day.days + 1
    #         elif to_date < end_date and to_date > start_date:
    #             day = to_date - start_date
    #             day = day.days + 1
    #         else:
    #             raise UserError(_('%s Invalid Contract!', contract.name))
    #         if day:
    #             contract_limit = day / slip_days
    #         localdict['contract'] = contract
    #         self.contract_id = contract.id
    #         rules_dict = localdict['rules'].dict
    #         result_rules_dict = localdict['result_rules'].dict
    #
    #         blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])
    #
    #         result = {}
    #
    #         for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
    #             if rule.id in blacklisted_rule_ids:
    #                 continue
    #             localdict.update({
    #                 'result': None,
    #                 'result_qty': 1.0,
    #                 'result_rate': 100,
    #                 'result_name': False
    #             })
    #             if rule._satisfy_condition(localdict):
    #                 amount, qty, rate = rule._compute_rule(localdict)
    #                 #check if there is already a rule computed with that code
    #                 previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
    #                 #set/overwrite the amount computed for this rule in the localdict
    #                 tot_rule = amount * qty * rate / 100.0
    #                 localdict[rule.code] = tot_rule
    #                 result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
    #                 rules_dict[rule.code] = rule
    #                 # sum the amount for its salary category
    #                 localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
    #                 # Retrieve the line name in the employee's lang
    #                 employee_lang = self.employee_id.sudo().address_home_id.lang
    #                 # This actually has an impact, don't remove this line
    #                 context = {'lang': employee_lang}
    #                 if localdict['result_name']:
    #                     rule_name = localdict['result_name']
    #                 elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION', 'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
    #                     if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
    #                         if rule.name == "Double Holiday Pay":
    #                             rule_name = _("Double Holiday Pay")
    #                         if rule.struct_id.name == "CP200: Employees 13th Month":
    #                             rule_name = _("Prorated end-of-year bonus")
    #                         else:
    #                             rule_name = _('Basic Salary')
    #                     elif rule.code == "GROSS":
    #                         rule_name = _('Gross')
    #                     elif rule.code == "DEDUCTION":
    #                         rule_name = _('Deduction')
    #                     elif rule.code == "REIMBURSEMENT":
    #                         rule_name = _('Reimbursement')
    #                     elif rule.code == 'NET':
    #                         rule_name = _('Net Salary')
    #                 else:
    #                     rule_name = rule.with_context(lang=employee_lang).name
    #                 # create/overwrite the rule in the temporary results
    #                 result[rule.code] = {
    #                     'sequence': rule.sequence,
    #                     'code': rule.code,
    #                     'name': rule_name,
    #                     'note': html2plaintext(rule.note),
    #                     'salary_rule_id': rule.id,
    #                     'contract_id': localdict['contract'].id,
    #                     'employee_id': localdict['employee'].id,
    #                     'amount': amount * contract_limit,
    #                     'quantity': qty,
    #                     'rate': rate,
    #                     'slip_id': self.id,
    #                 }
    #         if first_flag:
    #             result_dict = result.copy()
    #             first_flag = False
    #     if len(copy_localdict['contract']) > 1:
    #         for rule in set(result_dict):
    #             for key in set(result_dict.get(rule, 0)):
    #                 if key == 'amount':
    #                     result[rule][key] = result_dict.get(rule, 0).get(key, 0) + result.get(rule, 0).get(key, 0)
    #     payslip_worked_days_ids = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', self.id)])
    #     for payslip_worked_days_id in payslip_worked_days_ids:
    #         if payslip_worked_days_id.work_entry_type_id.id == 1:
    #             payslip_worked_days_id.amount = result['BASIC']['amount']
    #     return result.values()

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        attachment_types = self._get_attachment_types()
        attachment_type_ids = [f.id for f in attachment_types.values()]
        for slip in self:
            slip.update({'input_line_ids': [Command.unlink(line.id) for line in slip.input_line_ids]})
            if not slip.employee_id or not slip.employee_id.salary_attachment_ids or not slip.struct_id:
                lines_to_remove = slip.input_line_ids.filtered(lambda x: x.input_type_id.id in attachment_type_ids)
                slip.update({'input_line_ids': [Command.unlink(line.id) for line in lines_to_remove]})
            if slip.employee_id.salary_attachment_ids:
                lines_to_keep = slip.input_line_ids.filtered(lambda x: x.input_type_id.id not in attachment_type_ids)
                input_line_vals = [Command.clear()] + [Command.link(line.id) for line in lines_to_keep]

                valid_attachments = slip.employee_id.salary_attachment_ids.filtered(
                    lambda a: a.state == 'open' and a.date_start <= slip.date_to
                )

                # Only take deduction types present in structure
                deduction_types = list(set(valid_attachments.mapped('deduction_type')))
                struct_deduction_lines = list(set(slip.struct_id.rule_ids.mapped('code')))
                included_deduction_types = [f for f in deduction_types if attachment_types[f].code in struct_deduction_lines]
                for deduction_type in included_deduction_types:
                    if not slip.struct_id.rule_ids.filtered(lambda r: r.active and r.code == attachment_types[deduction_type].code):
                        continue
                    attachments = valid_attachments.filtered(lambda a: a.deduction_type == deduction_type)
                    amount = sum(attachments.mapped('active_amount'))
                    name = ', '.join(attachments.mapped('description'))
                    input_type_id = attachment_types[deduction_type].id
                    input_line_vals.append(Command.create({
                        'name': name,
                        'amount': amount,
                        'input_type_id': input_type_id,
                    }))
                slip.update({'input_line_ids': input_line_vals})

            if slip.employee_id and slip.struct_id and slip.contract_id and slip.date_from and slip.date_to:



                if not self._get_leave_count() and not self._get_late_count() and not self._get_early_out_count():
                    slip.update({'input_line_ids': [Command.create({
                            'name': 'Attendance Allowance',
                            'amount': self.employee_id.contract_id.first_attendance_allowance or 0,
                            'input_type_id': self.env.ref('hr_localization.other_input_type_attendance_alw').id,
                        })]})

                elif not self._get_leave_count() and self._get_late_count()<2 and self._get_early_out_count()<2:
                    slip.update({'input_line_ids': [Command.create({
                            'name': 'Attendance Allowance',
                            'amount': self.employee_id.contract_id.second_attendance_allowance or 0,
                            'input_type_id': self.env.ref('hr_localization.other_input_type_attendance_alw').id,
                        })]})

                if self._get_late_count()==4:
                    day=1
                    slip.update({'input_line_ids': [Command.create({
                            'name': 'Late Deduction',
                            'amount': (self.employee_id.contract_id.wage/monthrange(self.date_from.year, self.date_from.month)[1])*day or 0,
                            'input_type_id': self.env.ref('hr_localization.other_input_type_late_deduction').id,
                        })]})

                if self._get_late_count()>4:
                    day=1+((self._get_late_count()-4)*0.5)
                    slip.update({'input_line_ids': [Command.create({
                            'name': 'Late Deduction',
                            'amount': (self.employee_id.contract_id.wage/monthrange(self.date_from.year, self.date_from.month)[1])*day or 0,
                            'input_type_id': self.env.ref('hr_localization.other_input_type_late_deduction').id,
                        })]})

                if self._get_leave_count_partial():
                    slip.update({'input_line_ids': [Command.create({
                            'name': 'Leave Deduction',
                            'amount': (((self.contract_id.wage/self.days_of_month)*self._get_leave_count_partial()[0]['second_leave']) + ((self.second_contract_id.wage/self.days_of_month)*self._get_leave_count_partial()[0]['first_leave'])) or 0,
                            'input_type_id': self.env.ref('hr_localization.other_input_type_leave_deduction').id,
                        })]})

                if self._get_absent_count():
                    slip.update({'input_line_ids': [Command.create({
                            'name': 'Absence',
                            'amount': (((self.contract_id.wage/self.days_of_month)*self._get_absent_count()[0]['second_abs']) + ((self.second_contract_id.wage/self.days_of_month)*self._get_absent_count()[0]['first_abs'])) or 0,
                            'input_type_id': self.env.ref('hr_localization.other_input_type_absence').id,
                        })]})


                input_type_obj = self.env['hr.payslip.input.type']

                allowance = self.env['hr.allowance'].sudo().search([('employee_id', '=', self.employee_id.id),
                                                            ('effective_date', '<=', self.date_to), '|',
                                                            ('end_date', '=', False),
                                                            ('end_date', '>=', self.date_to)])

                if allowance:
                    for alw in allowance:
                        if alw.effective_type == 'one_time' and (alw.effective_date.month != self.date_from.month or alw.effective_date.year != self.date_from.year):
                            continue
                        elif alw.effective_type == 'yearly' and alw.effective_date.month != self.date_from.month:
                            continue
                        input_type = input_type_obj.search([('code', '=', alw.allowance_config_id.code)])
                        if input_type:

                            slip.update({'input_line_ids': [Command.create({
                            'name': input_type.name,
                            'amount': alw.amount or 0,
                            'input_type_id': input_type.id,
                            })]})


                deduction = self.env['hr.deduction'].sudo().search([('employee_id', '=', self.employee_id.id),
                                                            ('effective_date', '<=', self.date_to), '|',
                                                            ('end_date', '=', False),
                                                            ('end_date', '>=', self.date_to)])
                if deduction:
                    for ded in deduction:
                        if ded.effective_type == 'one_time' and (ded.effective_date.month != self.date_from.month or ded.effective_date.year != self.date_from.year):
                            continue
                        elif ded.effective_type == 'yearly' and ded.effective_date.month != self.date_from.month:
                            continue
                        input_type = input_type_obj.search([('code', '=', ded.deduction_config_id.code)])
                        if input_type:

                            slip.update({'input_line_ids': [Command.create({
                            'name': input_type.name,
                            'amount': ded.amount or 0,
                            'input_type_id': input_type.id,
                            })]})

                if not (slip.employee_id and slip.struct_id and slip.contract_id and slip.date_from and slip.date_to):
                    slip.update({'input_line_ids': [Command.unlink(line.id) for line in slip.input_line_ids]})







    def _get_leave_count(self):
        if self.employee_id:
            calendar = self.employee_id.resource_calendar_id
            tz = timezone(calendar.tz)

            leave_count=0
            date_start = tz.localize((fields.Datetime.to_datetime(self.date_from)).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            date_stop = tz.localize((fields.Datetime.to_datetime(self.date_to + timedelta(days=1))).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            # import pdb
            # pdb.set_trace()
            leave = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                        ('request_date_from', '>=', self.date_from),
                                                        ('request_date_to', '<=', self.date_to),
                                                        ('state','in',['validate','validate1'])]
                                                    )
            for count in leave:
                leave_count += count.number_of_days

            return leave_count


    def _get_leave_count_partial(self):
        if self.employee_id:
            calendar = self.employee_id.resource_calendar_id
            tz = timezone(calendar.tz)

            leave_count=[]
            first_leave=second_leave=0
            date_start = tz.localize((fields.Datetime.to_datetime(self.date_from)).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            date_stop = tz.localize((fields.Datetime.to_datetime(self.date_to + timedelta(days=1))).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            # import pdb
            # pdb.set_trace()
            leave = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                        ('request_date_from', '>=', self.date_from),
                                                        ('request_date_to', '<=', self.date_to),
                                                        ('state','in',['validate','validate1'])]
                                                    )
            for count in leave:
                if count.request_date_from<self.contract_id.date_start:
                    first_leave +=count.number_of_days
                else:
                    second_leave += count.number_of_days

            leave_count.append({'first_leave':first_leave,'second_leave':second_leave})

            return leave_count



    def _get_late_count(self):
        if self.employee_id:
            calendar = self.employee_id.resource_calendar_id
            tz = timezone(calendar.tz)

            ot_hour = ot_amount=0
            date_start = tz.localize((fields.Datetime.to_datetime(self.date_from)).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            date_stop = tz.localize((fields.Datetime.to_datetime(self.date_to + timedelta(days=1))).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            # import pdb
            # pdb.set_trace()
            late_deduction = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
                                                        ('check_in', '>=', date_start),

                                                        ('check_out', '<=', date_stop),
                                                        ('state', '=', 'approve'),('late_minutes','>',0.25)],
                                                    order='check_in asc')


            return len(late_deduction)


    def _get_early_out_count(self):
        if self.employee_id:
            calendar = self.employee_id.resource_calendar_id
            tz = timezone(calendar.tz)

            ot_hour = ot_amount=0
            date_start = tz.localize((fields.Datetime.to_datetime(self.date_from)).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            date_stop = tz.localize((fields.Datetime.to_datetime(self.date_to + timedelta(days=1))).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            # import pdb
            # pdb.set_trace()
            early_out = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
                                                        ('check_in', '>=', date_start),

                                                        ('check_out', '<=', date_stop),
                                                        ('state', '=', 'approve'),('early_out_minutes','>',0)],
                                                    order='check_in asc')


            return len(early_out)

    def _get_absent_count(self):
        if self.employee_id:
            calendar = self.employee_id.resource_calendar_id
            tz = timezone(calendar.tz)
            absent_count = []
            first_abs = second_abs =0
            date_start = tz.localize((fields.Datetime.to_datetime(self.date_from)).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            date_stop = tz.localize((fields.Datetime.to_datetime(self.date_to + timedelta(days=1))).replace(tzinfo=None), is_dst=True).astimezone(tz=UTC)
            absence = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
                                                        ('check_in', '>=', date_start),

                                                        ('check_out', '<=', date_stop),
                                                        ('state', '=', 'approve'),('is_absent','=',True)],
                                                    order='check_in asc')
            for count in absence:
                if count.check_in.date()<self.contract_id.date_start:
                    first_abs +=1
                else:
                    second_abs += 1

            absent_count.append({'first_abs':first_abs,'second_abs':second_abs})

            return absent_count




    # def _get_worked_day_lines(self):

    #     res = super(HrPayslip, self)._get_worked_day_lines(domain=None, check_out_of_contract=True)

    #     for val in res:
    #         entry_type = self.env['hr.work.entry.type'].search([('id','=',val.get('work_entry_type_id'))])
    #         if entry_type.code == 'OUT':
    #             res.append({
    #                 'amount': self.second_contract_id.wage,
                    
    #             })


    #     return res

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'


    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        #Prevent a payslip_run from having multiple payslips for the same employee
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            return success_result

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', employees.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }


        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []
        for contract in contracts:
            values = dict(default_values, **{
                'name': _('New Payslip'),
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslips_vals.append(values)
        for payslip in payslips_vals:
            payslips = Payslip.with_context(tracking_disable=True).create(payslip)
            payslips._compute_name()
            payslips.compute_sheet()
            payslip_run.state = 'verify'

        return success_result


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'


    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'payslip_id.normal_wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
            if not worked_days.contract_id:
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            elif worked_days.code == 'OUT':
                if worked_days.payslip_id.second_contract_id:
                    worked_days.amount = worked_days.payslip_id.second_contract_id.wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0
                else:
                    worked_days.amount = 0
            else:
                worked_days.amount = worked_days.payslip_id.normal_wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0



