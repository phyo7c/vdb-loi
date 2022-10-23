from odoo import fields, models, api, _
from datetime import datetime, timedelta



class HrLeaveAutoAllocation(models.Model):
    _inherit = 'hr.leave.auto.allocation'

    carried_forward = fields.Boolean(string='Carried Forward', default=False)
    prorated = fields.Boolean(string='Prorated' , default=False)
    prorated_based_on = fields.Selection([('join date', 'Join Date'),
                                 ('permanent', 'Permanent')], 'Prorated Based on', default='join date')

    def compute_leave_balance(self, employee_id, holiday_status_id):
        number_of_days = 0
        if employee_id and holiday_status_id:
            max_leaves = 0
            leaves_taken = 0
            today = fields.Date.today()
            prev_fiscal_year = self.env['account.fiscal.year'].sudo().search([('date_from', '<=', today), ('date_to', '>=', today)], limit=1)
            start_date = prev_fiscal_year.date_from
            end_date = prev_fiscal_year.date_to
            requests = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee_id),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id),
                ('request_date_from', '>=', start_date),
                ('request_date_to', '<=', end_date),
            ])

            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee_id),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id),
                ('fiscal_year', '=', prev_fiscal_year.id)
            ])

            for request in requests:
                leaves_taken += (request.number_of_hours_display
                                            if request.leave_type_request_unit == 'hour'
                                            else request.number_of_days)

            for allocation in allocations.sudo():
                max_leaves += (allocation.number_of_hours_display
                                            if allocation.type_request_unit == 'hour'
                                            else allocation.number_of_days)
            
            number_of_days = (max_leaves - leaves_taken) * 0.5
            if number_of_days % 0.5 != 0:
                number_of_days = round(number_of_days)
            if number_of_days >= 5:
                number_of_days = 5
        return number_of_days

    def _generate_leave_carried_forward(self, employee_ids=None):
        today = fields.Date.today()
        today_plus_one = today + timedelta(days=1)
        fiscal_year = self.env['account.fiscal.year'].sudo().search([('date_from', '<=', today), ('date_to', '>=', today)], limit=1)
        if fiscal_year and today == fiscal_year.date_to:
            allocation_obj = self.env['hr.leave.allocation'].sudo()
            auto_allocations = self.env['hr.leave.auto.allocation'].search([('state', '=', 'approve'), ('carried_forward', '=', True)])
            upcoming_fiscal_year = self.env['account.fiscal.year'].sudo().search([('date_from', '<=', today_plus_one), ('date_to', '>=', today_plus_one)], limit=1)
            
            # Change prev fiscal year carry leaves to expired state
            domain = []
            if employee_ids:
                employees = self.env['hr.employee'].sudo().search([('id', 'in', employee_ids)])
                domain = [('state', '=', 'validate'), ('employee_id', 'in', employees.ids), ('carry_leave', '=', True), ('fiscal_year', '=', fiscal_year.id)]
            else:
                domain = [('state', '=', 'validate'), ('carry_leave', '=', True), ('fiscal_year', '=', fiscal_year.id)]
            
            prev_carry_allocations = allocation_obj.search(domain)
            for allocation in prev_carry_allocations:
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
                    number_of_days = self.compute_leave_balance(emp.id, holiday_status.id)
                    existing_allocation = allocation_obj.search([
                        ('employee_id', '=', emp.id), 
                        ('state', '=', 'validate'), 
                        ('holiday_status_id', '=', holiday_status.id), 
                        ('fiscal_year', '=', upcoming_fiscal_year.id),
                        ('carry_leave', '=', True)
                    ])
                    if existing_allocation:
                        existing_allocation.action_refuse()
                        existing_allocation.action_draft()
                        existing_allocation.unlink()
                    if number_of_days > 0:
                        values = {
                                    'name': 'Auto Carried Forward',
                                    'holiday_status_id': holiday_status.id,
                                    'employee_id': emp.id,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'holiday_type': 'employee',
                                    'number_of_days': number_of_days,
                                    'fiscal_year': upcoming_fiscal_year.id,
                                    'carry_leave': True
                                }
                        leave_allocation = allocation_obj.create(values)
                        if leave_allocation:
                            leave_allocation.action_approve()
                            leave_allocation.action_validate()
                    
