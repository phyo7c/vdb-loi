from odoo import fields, models, api, _
from datetime import datetime, time, timedelta
from odoo.exceptions import UserError
import logging
from datetime import date

_logger = logging.getLogger(__name__)


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('expired', 'Expired')
        ], string='Status', readonly=True, tracking=True, copy=False, default='confirm')
    fiscal_year = fields.Many2one('account.fiscal.year', string='Fiscal Year', readonly=True)
    carry_leave = fields.Boolean(string='Carry Leave?', default=False, readonly=True)


class HrLeaveAutoAllocation(models.Model):
    _name = 'hr.leave.auto.allocation'
    _description = 'HR Leave Auto Allocation'
    _rec_name = 'holiday_status_id'

    holiday_status_id = fields.Many2one("hr.leave.type", string="Leave Type")
    employee_categ_ids = fields.Many2many('hr.employee.category', string='Employee Tags')
    state = fields.Selection([('draft', 'Draft'),
                              ('approval', 'Waiting Approval'),
                              ('approve', 'Approve'),
                              ('cancel', 'Cancel')], 'State', default='draft')
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other'),
                               ('all', 'All')], 'Gender', default='all')
    allocate_on = fields.Selection([('employee_tags', 'Employee Tags'),
                                    ('department', 'Department'),
                                    ('position', 'Position')], 'Allocate On', default='employee_tags')
    department_ids = fields.Many2many('hr.department', string='Departments')
    position_ids = fields.Many2many('hr.job', string='Job Position')
    based_on = fields.Selection([('join date', 'Join Date'),
                                 ('permanent', 'Permanent')], 'Based on', default='join date')
    validity_year_type = fields.Selection([('fiscal', 'Fiscal Year'),
                                           ('calendar', 'Calendar Year')], 'Validity Based On', default='fiscal')
    maximum_allocation_days = fields.Float('Maximum Allocation Days', default=1)
    deduct_based_on_worked_day = fields.Boolean('Deduct Based On Numbers of Days Per Month')
    minimum_worked_days_per_month = fields.Float('Minimum Number of Days Worked Per Month')
    validate_from = fields.Float('Validate From')

    def get_number_of_days(self, leave_type, employee_id):
        number_of_days = 0
        if leave_type and employee_id:
            number_of_days = leave_type.maximum_allocation_days
            if number_of_days > 0:
                if employee_id.state == 'probation':
                    current_date = fields.Date.today()
                    joined_date = employee_id.joining_date
                    total_month = (current_date.year - joined_date.year) * 12 + (current_date.month - joined_date.month) + 1
                    if total_month < 12:
                        per_month_count = number_of_days / 12
                        number_of_days = per_month_count * total_month
                        if number_of_days % 0.5 != 0:
                            number_of_days = round(number_of_days)
        return number_of_days
    
    def create_allocation(self, holiday_status, employee_id, date_from, date_to, number_of_days, fiscal_year):
        values = {
                    'name': holiday_status.name,
                    'holiday_status_id': holiday_status.id,
                    'employee_id': employee_id.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'holiday_type': 'employee',
                    'number_of_days': number_of_days,
                    'fiscal_year': fiscal_year.id,
                    'carry_leave': False,
                }
        leave_allocation = self.env['hr.leave.allocation'].sudo().create(values)
        if leave_allocation:
            # leave_allocation.action_approve()
            leave_allocation.action_validate()

    def _generate_leave_allocation(self, employee_ids=None):
        # import pdb
        # pdb.set_trace()
        allocation_obj = self.env['hr.leave.allocation'].sudo()
        fiscal_year_obj = self.env['account.fiscal.year'].sudo()
        attendance_obj = self.env['hr.attendance'].sudo()
        start_date_current_year = date(date.today().year, 1, 1)
        end_date_current_year = date(date.today().year, 12, 31)
        auto_allocations = self.env['hr.leave.auto.allocation'].search([('state', '=', 'approve')])
        today = fields.Date.today()
        today_plus_one = today + timedelta(days=1)
        fiscal_year = fiscal_year_obj.search([('date_from', '<=', today), ('date_to', '>=', today)], limit=1)
        upcoming_fiscal_year = fiscal_year_obj.search([('date_from', '<=', today_plus_one), ('date_to', '>=', today_plus_one)], limit=1)
        if fiscal_year and today == fiscal_year.date_to:
            domain = []
            if employee_ids:
                employees = self.env['hr.employee'].sudo().search([('id', 'in', employee_ids)])
                domain = [('state', '=', 'validate'), ('employee_id', 'in', employees.ids), ('carry_leave', '!=', True), ('fiscal_year', '=', fiscal_year.id)]
            else:
                domain = [('state', '=', 'validate'), ('carry_leave', '!=', True), ('fiscal_year', '=', fiscal_year.id)]
            
            prev_allocations = allocation_obj.search(domain)
            for allocation in prev_allocations:
                allocation.state = 'expired'
                allocation.fiscal_year = fiscal_year

            for auto in auto_allocations:
                holiday_status = auto.holiday_status_id
                date_from = upcoming_fiscal_year.date_from
                date_to = upcoming_fiscal_year.date_to
                emp_domain = []
                if employee_ids:
                    emp_domain = [('id', 'in', employee_ids)]
                else:
                    emp_domain = [('contract_id.state', '=', 'open')]
                    if auto.gender != 'all':
                        emp_domain += [('gender', '=', auto.gender)]
                    if auto.based_on == 'permanent':
                        emp_domain += [('state', '=', 'permanent')]
                    if auto.allocate_on == 'employee_tags':
                        emp_domain += [('category_ids', 'in', auto.employee_categ_ids.ids)]
                    elif auto.allocate_on == 'department':
                        emp_domain += [('department_id', 'in', auto.department_ids.ids)]
                    elif auto.allocate_on == 'position':
                        emp_domain += [('job_id', 'in', auto.position_ids.ids)]

                employees = self.env['hr.employee'].sudo().search(emp_domain)
                for emp in employees:

                    if not allocation_obj.search([('employee_id', '=', emp.id), ('holiday_status_id', '=', holiday_status.id), ('carry_leave', '!=', True), ('state', '=', 'validate'), ('fiscal_year', '=', upcoming_fiscal_year.id)]):
                        if holiday_status.allocation_validation_type != 'set':
                            number_of_days = auto.maximum_allocation_days
                            
                            if auto.prorated and auto.prorated_based_on == 'join date':
                                  
                                if auto.validity_year_type == 'fiscal':
                                    if auto.validate_from:
                                        validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                    else:
                                        validate_days = emp.joining_date
                                    if (date_from<validate_days and validate_days<date_to):
                                        number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    else:
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                else:
                                    if auto.validate_from:
                                        validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                    else:
                                        validate_days = emp.joining_date
                                    if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                        number_of_days = (number_of_days/12)*(13-validate_days.month)
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    else:
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                

                            elif auto.prorated and auto.prorated_based_on == 'permanent':
                                 
                                    if auto.permanent_date == 'fiscal' and emp.permanent_date:
                                        if auto.validate_from:
                                            validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                        else:
                                            validate_days = emp.permanent_date
                                        if (date_from<validate_days and validate_days<date_to):
                                            number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                            # print('hello')
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    else:
                                        if auto.validate_from:
                                            validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                        else:
                                            validate_days = emp.permanent_date
                                        if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                            number_of_days = (number_of_days/12)*(13-validate_days.month)
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                

                            else:        
                                number_of_days = self.get_number_of_days(auto, emp)
                                if number_of_days > 0:
                                    self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, upcoming_fiscal_year)
                        else:
                            if emp.state == 'permanent':
                                number_of_days = auto.maximum_allocation_days
                                if auto.prorated and auto.prorated_based_on == 'join date':
                                     
                                        if auto.validity_year_type == 'fiscal':
                                            if auto.validate_from:
                                                validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.joining_date
                                            if (date_from<validate_days and validate_days<date_to):
                                                number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                                # print('hello')
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            if auto.validate_from:
                                                validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.joining_date
                                            if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                                number_of_days = (number_of_days/12)*(13-validate_days.month)
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    

                                elif auto.prorated and auto.prorated_based_on == 'permanent':

                                        if auto.validity_year_type == 'fiscal':
                                            if auto.validate_from:
                                                validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.permanent_date
                                            if (date_from<validate_days and validate_days<date_to):
                                                number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                                # print('hello')
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            if auto.validate_from:
                                                validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.permanent_date
                                            if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                                number_of_days = (number_of_days/12)*(13-validate_days.month)
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    
                                else:
                                    number_of_days = self.get_number_of_days(auto, emp)
                                    if number_of_days > 0:
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, upcoming_fiscal_year)
                    else:
                        existing_allocation = allocation_obj.search([
                            ('employee_id', '=', emp.id), 
                            ('state', '=', 'validate'), 
                            ('holiday_status_id', '=', holiday_status.id), 
                            ('fiscal_year', '=', upcoming_fiscal_year.id),
                            ('carry_leave', '!=', True)
                        ])
                        if existing_allocation:
                            number_of_days = self.get_number_of_days(auto, emp)
                            existing_allocation.write({'number_of_days': number_of_days})
        else:
            for auto in auto_allocations:
                holiday_status = auto.holiday_status_id
                date_from = fiscal_year.date_from
                date_to = fiscal_year.date_to
                if auto.validity_year_type == 'fiscal':
                    prev_year = fiscal_year_obj.search([('date_to', '<=', date_from)], order='date_to desc', limit=1)
                    if prev_year:
                        prev_year_start = prev_year.date_from
                        prev_year_stop = prev_year.date_to + timedelta(days=1)
                    else:
                        prev_year_start = date_from.replace(year=date_from.year - 1)
                        prev_year_stop = date_to.replace(year=date_to.year - 1)
                else:
                    prev_year = date_from.year - 1
                    prev_year_start = datetime.strptime(str(prev_year) + '-01-01', '%Y-%m-%d')
                    prev_year_stop = datetime.strptime(str(date_from.year) + '-01-01', '%Y-%m-%d')
                
                emp_domain = []
                if employee_ids:
                    emp_domain = [('id', 'in', employee_ids)]
                else:
                    emp_domain = [('contract_id.state', '=', 'open')]
                    if auto.gender != 'all':
                        emp_domain += [('gender', '=', auto.gender)]
                    if auto.based_on == 'permanent':
                        emp_domain += [('state', '=', 'permanent')]
                    if auto.allocate_on == 'employee_tags':
                        emp_domain += [('category_ids', 'in', auto.employee_categ_ids.ids)]
                    elif auto.allocate_on == 'department':
                        emp_domain += [('department_id', 'in', auto.department_ids.ids)]
                    elif auto.allocate_on == 'position':
                        emp_domain += [('job_id', 'in', auto.position_ids.ids)]
                # import pdb
                # pdb.set_trace()
                employees = self.env['hr.employee'].sudo().search(emp_domain)
                for emp in employees:
                    if not allocation_obj.search([('employee_id', '=', emp.id), ('holiday_status_id', '=', holiday_status.id), ('carry_leave', '!=', True), ('state', '=', 'validate')]):
                        if holiday_status.allocation_validation_type != 'set':
                            number_of_days = auto.maximum_allocation_days
                            if auto.prorated and auto.prorated_based_on == 'join date':
                                 
                                    if auto.validity_year_type == 'fiscal':
                                        if auto.validate_from:
                                            validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                        else:
                                            validate_days = emp.joining_date
                                        if (date_from<validate_days and validate_days<date_to):
                                            number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                            # print('hello')
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    else:
                                        if auto.validate_from:
                                            validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                        else:
                                            validate_days = emp.joining_date
                                        if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                            number_of_days = (number_of_days/12)*(13-validate_days.month)
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                

                            elif auto.prorated and auto.prorated_based_on == 'permanent':
                                    if auto.validity_year_type == 'fiscal':
                                        if auto.validate_from:
                                            validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                        else:
                                            validate_days = emp.permanent_date
                                        if (date_from<validate_days and validate_days<date_to):
                                            number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                            # print('hello')
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    else:
                                            if auto.validate_from:
                                                validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.permanent_date
                                            if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                                number_of_days = (number_of_days/12)*(13-validate_days.month)
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                

                            else:
                                if auto.deduct_based_on_worked_day:
                                    atten_domain = [('check_in', '>=', prev_year_start),
                                                    ('check_in', '<', prev_year_stop),
                                                    ('employee_id', '=', emp.id)]
                                    attendances = attendance_obj.read_group(atten_domain, ['employee_id'], ['check_in:month'], lazy=False)
                                    absence = 12 - len(attendances)

                                    for atten in attendances:
                                        if atten['__count'] < auto.minimum_worked_days_per_month:
                                            absence += 1

                                    number_of_days -= (absence / 12) * number_of_days

                                if number_of_days > 0:
                                    current_date = fields.Date.today()
                                    joined_date = emp.joining_date
                                    if auto.validate_from:
                                        if current_date >= emp.joining_date + timedelta(days=auto.validate_from):
                                            # total_month = (current_date.year - joined_date.year) * 12 + (current_date.month - joined_date.month) + 1
                                            # if total_month < 12:
                                            #     per_month_count = number_of_days / 12
                                            #     number_of_days = per_month_count * total_month
                                            #     if number_of_days % 0.5 != 0:
                                            #         number_of_days = round(number_of_days)
                                            number_of_days = auto.maximum_allocation_days
                                            self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    else:
                                        # total_month = (current_date.year - joined_date.year) * 12 + (current_date.month - joined_date.month) + 1
                                        # if total_month < 12:
                                        #     per_month_count = number_of_days / 12
                                        #     number_of_days = per_month_count * total_month
                                        #     if number_of_days % 0.5 != 0:
                                        #         number_of_days = round(number_of_days)
                                        number_of_days = auto.maximum_allocation_days
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                        else:
                            if emp.state == 'permanent':
                                number_of_days = auto.maximum_allocation_days
                                if auto.prorated and auto.prorated_based_on == 'join date':

                                        if auto.validity_year_type == 'fiscal':
                                            if auto.validate_from:
                                                validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.joining_date
                                            if (date_from<validate_days and validate_days<date_to):
                                                number_of_days = (number_of_days/12)*(13-validate_days.month + date_to.month) #((date_to.month+1)-emp.joining_date.month)
                                                if number_of_days % 0.5 != 0:
                                                    number_of_days = round(number_of_days)
                                                # print('hello')
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            if auto.validate_from:
                                                validate_days = emp.joining_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.joining_date
                                            if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                                number_of_days = (number_of_days/12)*(13-validate_days.month)
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    

                                elif auto.prorated and auto.prorated_based_on == 'permanent':
                                     
                                        if auto.validity_year_type == 'fiscal':
                                            if auto.validate_from:
                                                validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.permanent_date
                                            if (date_from<validate_days and validate_days<date_to):
                                                number_of_days = (number_of_days/12)*((date_to.month+1)-validate_days.month)
                                                # print('hello')
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                        else:
                                            if auto.validate_from:
                                                validate_days = emp.permanent_date + timedelta(days=auto.validate_from)
                                            else:
                                                validate_days = emp.permanent_date
                                            if (start_date_current_year<validate_days and validate_days<end_date_current_year):
                                                number_of_days = (number_of_days/12)*(13-emp.permanent_date.month)
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                            else:
                                                self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)
                                    

                                else:
                                    if auto.deduct_based_on_worked_day:
                                        atten_domain = [('check_in', '>=', prev_year_start),
                                                        ('check_in', '<', prev_year_stop),
                                                        ('employee_id', '=', emp.id)]
                                        attendances = attendance_obj.read_group(atten_domain, ['employee_id'], ['check_in:month'], lazy=False)
                                        absence = 12 - len(attendances)

                                        for atten in attendances:
                                            if atten['__count'] < auto.minimum_worked_days_per_month:
                                                absence += 1

                                        number_of_days -= (absence / 12) * number_of_days

                                    if number_of_days > 0:
                                        current_date = fields.Date.today()
                                        joined_date = emp.joining_date
                                        total_month = (current_date.year - joined_date.year) * 12 + (current_date.month - joined_date.month) + 1
                                        if total_month < 12:
                                            per_month_count = number_of_days / 12
                                            number_of_days = per_month_count * total_month
                                            if number_of_days % 0.5 != 0:
                                                number_of_days = round(number_of_days)
                                        self.create_allocation(holiday_status, emp, date_from, date_to, number_of_days, fiscal_year)

                    else:
                        existing_allocation = allocation_obj.search([
                            ('employee_id', '=', emp.id), 
                            ('state', '=', 'validate'), 
                            ('holiday_status_id', '=', holiday_status.id), 
                            ('fiscal_year', '=', upcoming_fiscal_year.id),
                            ('carry_leave', '!=', True)
                        ])
                        if existing_allocation:
                            number_of_days = self.get_number_of_days(auto, emp)
                            existing_allocation.write({'number_of_days': number_of_days})
            
    def action_confirm(self):
        self.write({'state': 'approval'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.constrains('holiday_status_id', 'employee_categ_ids')
    def _check_duplicate_records(self):
        if self.holiday_status_id and self.employee_categ_ids:
            domain = [('id', '!=', self.id),
                      ('holiday_status_id', '=', self.holiday_status_id.id),
                      ('employee_categ_ids', 'in', self.employee_categ_ids.ids)]
            if self.search_count(domain) > 0:
                raise UserError(_('Duplicate record found!'))


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    def get_employees_leave_days(self, employee_ids):
        today = fields.Date.today()
        current_fiscal_year = self.env['account.fiscal.year'].sudo().search([('date_from', '<=', today), ('date_to', '>=', today)], limit=1)
        start_date = current_fiscal_year.date_from
        end_date = current_fiscal_year.date_to
        result = {
            employee_id: {
                leave_type.id: {
                    'max_leaves': 0,
                    'leaves_taken': 0,
                    'remaining_leaves': 0,
                    'virtual_remaining_leaves': 0,
                } for leave_type in self
            } for employee_id in employee_ids
        }

        requests = self.env['hr.leave'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids),
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date),
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        for request in requests:
            status_dict = result[request.employee_id.id][request.holiday_status_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                            if request.leave_type_request_unit == 'hour'
                                            else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)

        for allocation in allocations.sudo():
            status_dict = result[allocation.employee_id.id][allocation.holiday_status_id.id]
            if allocation.state == 'validate':
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                        if allocation.type_request_unit == 'hour'
                                                        else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                            if allocation.type_request_unit == 'hour'
                                            else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                if allocation.type_request_unit == 'hour'
                                                else allocation.number_of_days)
                
        return result

