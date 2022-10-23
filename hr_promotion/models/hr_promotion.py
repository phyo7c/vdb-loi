from odoo import api, fields, models, _
from datetime import date, timedelta
from pytz import timezone, UTC
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class Employee(models.Model):
    _inherit = 'hr.employee'

    approve_manager = fields.Many2one('hr.employee', string='Approve Manager', check_company=False,track_visibility='always')

class Contract(models.Model):    
    _inherit = 'hr.contract'    
    
    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        """ Two contracts in state [incoming | open | close] cannot overlap """
        for contract in self.filtered(lambda c: (c.state not in ['draft', 'close', 'cancel'] or c.state == 'draft' and c.kanban_state == 'done') and c.employee_id):
            domain = [
                ('id', '!=', contract.id),
                ('employee_id', '=', contract.employee_id.id),
                '|',
                    ('state', 'in', ['open']),
                    '&',
                        ('state', '=', 'draft'),
                        ('kanban_state', '=', 'done') # replaces incoming
            ]

            if not contract.date_end:
                start_domain = []
                end_domain = ['|', ('date_end', '>=', contract.date_start), ('date_end', '=', False)]
            else:
                start_domain = [('date_start', '<=', contract.date_end)]
                end_domain = ['|', ('date_end', '>', contract.date_start), ('date_end', '=', False)]

            domain = expression.AND([domain, start_domain, end_domain])
            if self.search_count(domain):
                raise ValidationError(
                    _(
                        'An employee can only have one contract at the same time. (Excluding Draft and Cancelled contracts).\n\nEmployee: %(employee_name)s',
                        employee_name=contract.employee_id.name
                    )
                )
class EmployeePromotion(models.Model):
    _name = 'hr.promotion'
    _description = 'Promotions'
    
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], order='id desc', limit=1).id
    
    name = fields.Char(string='Name', copy=False, default="/", readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string='Effective Date', default=fields.Date.today(), help="Date")
    state = fields.Selection([('draft', 'New'),
                              ('request', ' Requested'),
                              ('first_approve', 'First Approved'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done')], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    note = fields.Text(string='Internal Notes')
    promotion_no = fields.Char(string='Promotion NO')
    responsible = fields.Many2one('hr.employee', string='Responsible', default=_default_employee, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    #branch_id = fields.Many2one('res.branch', string='Branch')
    department_id = fields.Many2one('hr.department', 'Department')
    job_id = fields.Many2one('hr.job', 'Job Position')
    job_grade_id = fields.Many2one('job.grade', string='Job Grade')
    salary_level_id = fields.Many2one('salary.level', string='Salary Level')
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Hour')
    wage = fields.Float('Wage')
    approved_manager_id = fields.Many2one('hr.employee', string='Approved Manager')
    new_company_id = fields.Many2one('res.company', string='New Company', copy=False, required=True, default=lambda self: self.env.company)
    #new_branch_id = fields.Many2one('res.branch', string='New Branch')
    new_department_id = fields.Many2one('hr.department', 'New Department')
    new_job_id = fields.Many2one('hr.job', 'New Job Position')
    new_job_grade_id = fields.Many2one('job.grade', string='New Job Grade')
    new_salary_level_id = fields.Many2one('salary.level', string='New Salary Level')
    new_wage = fields.Float('New Wage')
    new_struct_id = fields.Many2one('hr.payroll.structure', string='New Salary Structure')
    requested_employee_id = fields.Many2one('hr.employee', string='Requested Person')
    approved_employee_id = fields.Many2one('hr.employee', string='Approved Person')
    type = fields.Selection([('promotion', 'Promotion'), ('demotion', 'Demotion'), ('transfer', 'Transfer'), ('salary_change', 'Salary Change')], 'Type', default='promotion', copy=False)
    allow_immediate_approve = fields.Boolean('Immediate Approve', compute='_allow_approve')
    new_approved_manager_id = fields.Many2one('hr.employee', string='New Approved Manager')
    new_resource_calendar_id = fields.Many2one('resource.calendar', string='New Working Hour')
    skip_head_count = fields.Boolean('Skip Employee Head Count', default=False,copy=False)

    @api.depends('date')
    def _allow_approve(self):
        local = self._context.get('tz', 'Asia/Yangon')
        local_tz = timezone(local)
        today_date = UTC.localize(fields.Datetime.now(), is_dst=True).astimezone(tz=local_tz).date()
        for rec in self:
            if rec.date <= today_date:
                rec.allow_immediate_approve = True
            else:
                rec.allow_immediate_approve = False

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            employee = self.employee_id
            #self.branch_id = employee.branch_id.id
            self.department_id = employee.department_id.id
            self.job_id = employee.job_id.id
            self.company_id = employee.company_id.id
            #self.new_branch_id = employee.branch_id.id
            self.new_department_id = employee.department_id.id
            self.new_job_id = employee.job_id.id
            self.new_company_id = employee.company_id.id
            self.approved_manager_id = employee.approve_manager.id
            self.new_approved_manager_id = employee.approve_manager.id
            self.resource_calendar_id = employee.resource_calendar_id.id
            if employee.contract_ids:
                contract = self.env['hr.contract'].search([('id', 'in', employee.contract_ids.ids), ('state', '=', 'open')], order='date_start desc', limit=1)
                self.job_grade_id = None
                self.salary_level_id = None
                self.struct_id = contract.structure_type_id.default_struct_id.id
                if self.company_id == self.new_company_id:
                    self.new_struct_id = contract.structure_type_id.default_struct_id.id
                self.wage = contract.wage
                self.new_job_grade_id = None
                self.new_salary_level_id = None
                self.new_resource_calendar_id = contract.resource_calendar_id.id

    @api.onchange('new_job_grade_id', 'new_salary_level_id')
    def _onchange_job_grade_level(self):
        if self.new_job_grade_id and self.new_salary_level_id:
            salary = self.env['hr.salary'].search([('job_grade_id', '=', self.new_job_grade_id.id),
                                                   ('salary_level_id', '=', self.new_salary_level_id.id)],
                                                  order='id desc', limit=1)
            if salary:
                self.new_wage = salary.salary
    
    @api.model
    def create(self, vals):
        employee = self.env['hr.employee'].browse(vals['employee_id'])
        if vals.get('type') == 'transfer':
            vals['name'] = "Transfer of " + employee.name
            promotion_no = self.env['ir.sequence'].next_by_code('transfer.code')
        elif vals.get('type') == 'salary_change':
            vals['name'] = "Changing Salary of " + employee.name
            promotion_no = self.env['ir.sequence'].next_by_code('salary.change.code')
        else:
            vals['name'] = "Promotion of " + employee.name
            promotion_no = self.env['ir.sequence'].next_by_code('promotion.code')
        if promotion_no:
            vals['promotion_no'] = promotion_no
        res = super(EmployeePromotion, self).create(vals)
        if vals['company_id'] != vals['new_company_id']  or vals['department_id'] != vals['new_department_id'] or vals['job_id'] != vals['new_job_id']:
            new_job = self.env['hr.job'].sudo().browse(vals['new_job_id'])
#             job_line = self.env['job.line'].sudo().search([('job_id', '=', vals['new_job_id']),
#                                                             ('company_id', '=', vals['new_company_id']),
#                                                             ('department_id', '=', vals['new_department_id'])], limit=1)
            same_position_resign_employee = self.env['hr.employee'].sudo().search([('job_id', '=', vals['new_job_id']),
                                                                                    ('company_id', '=', vals['new_company_id']),
                                                                                    ('department_id', '=', vals['new_department_id']),
                                                                                    ('resign_date', '!=', False)])
            if vals['skip_head_count'] == True:
                return res
            #if job_line and job_line.total_employee <= job_line.current_employee and not same_position_resign_employee:
#             if job_line and job_line.new_employee <= 0 and not same_position_resign_employee:
#                 raise ValidationError(_('Cannot Create New Employee for %s Position. Expected New Employee Zero.') % (new_job.name))

        return res

    def button_first_approve(self,employee_id=None):
        self.state = 'first_approve'
        if self.approved_manager_id.id == self.new_approved_manager_id.id:
            self.button_approve(employee_id=employee_id)

    def button_approve(self, employee_id=None):
        source = self._context.get('source', False) or False
        local = self._context.get('tz', 'Asia/Yangon')
        local_tz = timezone(local)
        current_date = UTC.localize(fields.Datetime.now(), is_dst=True).astimezone(tz=local_tz)
        if self.date > current_date.date() and source and source == 'schedule':
            return        
        if not employee_id:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], order='id desc', limit=1).id
        self.approved_employee_id = employee_id

        context = {
            "lang": "en_US", "active_model": "hr.promotion"
        }
        self.employee_id.with_context(context).write({
            'company_id': self.new_company_id.id,
            'department_id': self.new_department_id.id,
            'job_id': self.new_job_id.id,
            'parent_id': self.new_department_id.manager_id.id,
            #'manager_job_id': self.new_department_id.job_id.id,
            'approve_manager': self.new_approved_manager_id.id,
            'job_title':self.new_job_id.name,
            'resource_calendar_id':self.new_resource_calendar_id.id,
        })
#         resume_line = self.env['hr.resume.line'].search([('employee_id','=',self.employee_id.id)], order='id desc', limit=1)
#         if resume_line:
#             resume_line.write({'date_end':self.date - timedelta(days=1),
#                                'description': self.company_id.name + ' / ' + self.department_id.complete_name
#                                })
#             line_id = self.env['hr.resume.line'].sudo().create(
#                 {'name': self.new_job_id.name,
#                  'date_start': self.date,
#                  'employee_id' : self.employee_id.id,
#                  'line_type_id':1,
#                  'display_type':'classic',
#                  'description': self.new_company_id.name + ' / ' + self.new_department_id.complete_name
#                  }
#             )
#         if self.department_id and self.new_department_id and self.department_id.id != self.new_department_id.id and self.employee_id.id == self.department_id.manager_id.id:
#             self.department_id.write({'manager_id':False})

        if self.company_id != self.new_company_id:
            self.employee_id.user_id.company_ids = [(4, self.new_company_id.id)] 
            self.employee_id.user_id.company_id = self.new_company_id.id
            self.employee_id.address_home_id.company_id = self.new_company_id.id
            self.employee_id.address_id = self.new_company_id.partner_id.id if self.new_company_id.partner_id else False
            self.employee_id.work_email = self.new_company_id.email
            self.employee_id.work_phone = self.new_company_id.phone
#             for loan in self.env['hr.loan'].sudo().search([('employee_id','=',self.employee_id.id),('company_id','=',self.company_id.id)
#                                        ,('balance_amount','>',0),('state','=','approve')]):
#                 treasury_account = loan_account = journal = False
#                 treasury_account = self.env['account.account'].sudo().search([('code','=',loan.treasury_account_id.code),('company_id','=',self.new_company_id.id)],limit=1)
#                 #loan_account = self.env['account.account'].sudo().search([('code','=',loan.loan_account_id.code),('company_id','=',self.new_company_id.id)],limit=1)
#                 emp_account = self.env['account.account'].sudo().search([('code','=',loan.emp_account_id.code),('company_id','=',self.new_company_id.id)],limit=1)
#                 journal = self.env['account.journal'].sudo().search([('code','=',loan.journal_id.code),('company_id','=',self.new_company_id.id)],limit=1)
#                 loan_data = {
#                              'company_id':self.new_company_id.id,
#                              'department_id':self.new_department_id.id,
#                              'treasury_account_id':treasury_account.id or False,                             
#                              #'move_id':False,
#                              'emp_account_id':emp_account.id or False,
#                              'journal_id':journal.id or False,
#                              }
#                 loan.sudo().write(loan_data)
            
        contract = self.env['hr.contract'].search([('id', 'in', self.employee_id.contract_ids.ids), ('state', '=', 'open')], order='date_start desc', limit=1)
        contract_values = {'company_id': self.new_company_id.id,
                           'department_id': self.new_department_id.id,
                           'job_id': self.new_job_id.id,
                           #'job_grade_id': self.new_job_grade_id.id,
                           #'salary_level_id': self.new_salary_level_id.id,
                           'resource_calendar_id': self.employee_id.resource_calendar_id.id or False,
                           'wage': self.new_wage,
                           'date_start': self.date,
                           'state': 'open',
                           'date_end': False,
                           'structure_type_id':contract.structure_type_id.id or False,
                          # 'struct_id':self.new_struct_id.id or False,
                           'resource_calendar_id':self.new_resource_calendar_id.id or False,
                           'hr_responsible_id': self.env.uid}
        if contract:
            contract.write({'state': 'close', 'date_end': self.date - timedelta(days=1)})
            new_contract = contract.copy(contract_values)
        else:
            contract_values.update({'employee_id': self.employee_id.id,
                                    'name': 'Contract of ' + self.employee_id.name,
                                    'resource_calendar_id': self.employee_id.resource_calendar_id.id or False})
            new_contract = self.env['hr.contract'].create(contract_values)
        self.state = 'approve'
        
    def cancel_request(self):
        self.state = 'cancel'

    def button_done(self):
        self.state = 'done'

    def button_draft(self):
        self.state = 'draft'
        
    def button_request(self, employee_id=None):
        if not employee_id:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], order='id desc', limit=1).id
        self.requested_employee_id = employee_id
        self.state = 'request'
#         if self.employee_id.branch_id.manager_id:
#             one_signal_values = {'employee_id': self.employee_id.branch_id.manager_id.id,
#                                 'contents': _('EMPLOYEE CHANGES : To Approve Employee Changes %s') % (self.name),
#                                 'headings': _('WB B2B : APPROVAL EMPLOYEE CHANGES REQUEST')}
#             # self.env['one.signal.notification.message'].create(one_signal_values)

    @api.constrains('new_job_id')
    def constrain_new_job(self):
        for rec in self:
            if rec.type == 'salary_change' or rec.skip_head_count == True:
                return True
            #if rec.new_job_id.id != rec.job_id.id:
            if rec.new_job_id.id:
                job_line = self.env['hr.job'].sudo().search([('id', '=', rec.new_job_id.id)])
                if not job_line:
                    raise ValidationError(_('%s position at %s, %s, %s is not expecting new employee.') % (rec.new_job_id.name, rec.new_department_id.complete_name,
                                                                                                           rec.new_company_id.name))

#                 if job_line and job_line.new_employee <= 0:
#                     raise ValidationError(_('%s position at %s, %s, %s is not expecting new employee.') % (rec.new_job_id.name, rec.new_department_id.complete_name, rec.new_company_id.name))