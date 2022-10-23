from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrJob(models.Model):
    _inherit = 'hr.job'

    @api.depends('job_line.total_employee')
    def compute_total_employee(self):
        for job in self:
            total_emp = 0
            for line in job.job_line:
                total_emp = total_emp + line.total_employee
            job.total_employee = total_emp

    @api.depends('total_employee', 'current_employee')
    def compute_total_new_employee(self):
        for rec in self:
            rec.no_of_recruitment = 0
            if rec.total_employee >= rec.current_employee:
                rec.no_of_recruitment = rec.total_employee - rec.current_employee

    @api.depends('job_line.current_employee')
    def compute_current_employee(self):
        for job in self:
            total_current_emp = 0

            for line in job.job_line:
                current_employee = self.env['hr.employee'].search_count([('company_id', '=', line.company_id.id),
                                                                         ('branch_id', '=', line.branch_id.id),
                                                                         ('department_id', '=', line.department_id.id),
                                                                         ('resign_date', '=', False),
                                                                         ('job_id', '=', line.job_id.id)])
                total_current_emp = total_current_emp + current_employee
            job.current_employee = total_current_emp

    @api.constrains('job_line')
    def _constrains_job_line(self):
        if self.job_line:
            for line in self.job_line:
                new_emp = line.total_employee - line.current_employee
                if new_emp < 0:
                    raise ValidationError(_('Expected New Employee is Less Than Zero.'))

    total_employee = fields.Integer(string='Expected Total Employee', compute='compute_total_employee')
    new_employee = fields.Integer(string='Expected New Employee')
    current_employee = fields.Integer(string='Current Employee', compute='compute_current_employee')
    job_grade_id = fields.Many2one('job.grade', string='Job Grade')
    job_line = fields.One2many('job.line', 'job_id', string='Job')
    no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
                                       help='Number of new employees you expect to recruit.',
                                       compute='compute_total_new_employee')
    branch_id = fields.Many2one('res.branch', string='Branch')
    company_id = fields.Many2one('res.company', string='Company', default=False)
    jd_summary = fields.Char(string='JD Summary')


class JobLine(models.Model):
    _name = 'job.line'
    #_rec_name = 'job_id'

    @api.depends('company_id', 'branch_id', 'department_id', 'job_id')
    def _get_current_employee(self):
        for line in self:
            current_employee = 0
            if line.company_id and line.job_id:
                current_employee = self.env['hr.employee'].search_count([('company_id', '=', line.company_id.id),
                                                                         ('branch_id', '=', line.branch_id.id),
                                                                         ('department_id', '=', line.department_id.id),
                                                                         ('resign_date', '=', False),
                                                                         ('job_id', '=', line.job_id.id)])
            line.current_employee = current_employee

    @api.depends('total_employee', 'current_employee')
    def _get_new_employee(self):
        for line in self:
            line.new_employee = line.total_employee - line.current_employee
            line.expected_new_employee = line.new_employee


    job_id = fields.Many2one('hr.job', string='Job', index=True, required=True, ondelete='cascade')

    company_id = fields.Many2one('res.company', string='Company')
    branch_id = fields.Many2one('res.branch', string='Branch')
    department_id = fields.Many2one('hr.department', string='Department')
    total_employee = fields.Integer(string='Expected Total Employee')
    current_employee = fields.Integer(compute='_get_current_employee', string='Current Employee', readonly=True)
    new_employee = fields.Integer(compute='_get_new_employee', string='Expected New Employee', readonly=True)
    expected_new_employee = fields.Integer(string='New Employee')
    upper_position = fields.Many2one('hr.job', string='Upper Position')

    def write(self, vals):
        old_job_id = old_manager_id = False
        employee_obj = self.env['hr.employee'].sudo()
        job_line_obj = self.env['job.line'].sudo()
        department_obj = self.env['hr.department'].sudo()
        for rec in self:
            old_job_id = rec.job_id.id
            old_upper_position_id = rec.upper_position.id
            branch_id = rec.branch_id.id
            company_id = rec.company_id.id

            job_emp_ids = employee_obj.sudo().search(
                [('company_id', '=', company_id), ('branch_id', '=', branch_id), ('job_id', '=', old_job_id)])
            result = super(JobLine, self).write(vals)
            res = self.browse([rec.id])

            if old_upper_position_id != res.upper_position.id:
                if old_job_id and branch_id and company_id:
                    for employee in job_emp_ids:
                        if res.upper_position:
                            emp_direct_mng = employee_obj.sudo().search(
                                [('company_id', '=', company_id), ('branch_id', '=', branch_id),
                                 ('job_id', '=', res.upper_position.id)], limit=1)

                            # if emp_direct_mng :
                            #     employee.write({'parent_id': emp_direct_mng,'manager_job_id': job_line.upper_position.id})
                            if emp_direct_mng:
                                employee.write(
                                    {'manager_job_id': res.upper_position.id, 'parent_id': emp_direct_mng.id})
