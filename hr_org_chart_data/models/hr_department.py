from odoo import fields, models, api, _


class Department(models.Model):
    _inherit = 'hr.department'

    job_id = fields.Many2one('hr.job', string='Job Position')
    branch_id = fields.Many2one('res.branch', string='Branch')

    @api.onchange('job_id')
    def on_change_job_id(self):
        if self.job_id and self.company_id and self.branch_id:
            self.manager_id = self.env['hr.employee'].search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                ('job_id', '=', self.job_id.id)
            ], limit=1)
        else:
            self.manager_id = None

    def write(self, vals):
        old_job_id = old_manager_id = False
        employee_obj = self.env['hr.employee'].sudo()
        job_line_obj = self.env['job.line'].sudo()
        for rec in self:
            old_job_id = rec.job_id.id
            old_manager_id = rec.manager_id.id
            branch_id = rec.branch_id.id
            company_id = rec.company_id.id
            department_id = rec.id
            # approve_manager_id = rec.approve_manager
            mng_emp_ids = employee_obj.sudo().search(
                [('company_id', '=', company_id), ('branch_id', '=', branch_id), ('department_id', '=', department_id)])
            job_emp_ids = employee_obj.sudo().search(
                [('company_id', '=', company_id), ('branch_id', '=', branch_id), ('department_id', '=', department_id),
                 ('job_id', '=', old_job_id)])
            result = super(Department, self).write(vals)
            res = self.browse([rec.id])
            # import pdb
            # pdb.set_trace()
            if old_manager_id != res.manager_id.id:
                for employee in mng_emp_ids:
                    if employee.id != old_manager_id:
                        if vals.get('manager_id'):
                            # employee.write({'parent_id':vals.get('manager_id')})
                            emp = employee_obj.sudo().browse([vals.get('manager_id')])
                            if employee.id != vals.get('manager_id'):
                                # employee.write({'manager_job_id': emp.job_id.id, 'parent_id': vals.get('manager_id'),
                                #                 'approve_manager': res.approve_manager.id})
                                employee.write({'manager_job_id': emp.job_id.id, 'parent_id': vals.get('manager_id')})
                            else:
                                job_line = job_line_obj.sudo().search(
                                    [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
                                     ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
                                if job_line and job_line.upper_position:
                                    direct_mng = employee_obj.sudo().search(
                                        [('company_id', '=', job_line.company_id.id),
                                         ('branch_id', '=', job_line.branch_id.id),
                                         ('job_id', '=', job_line.upper_position.id)], limit=1)
                                    if direct_mng:
                                        employee.write(
                                            {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id})
                        else:
                            job_line = job_line_obj.sudo().search(
                                [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
                                 ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
                            if job_line and job_line.upper_position:
                                direct_mng = employee_obj.sudo().search(
                                    [('company_id', '=', job_line.company_id.id),
                                     ('branch_id', '=', job_line.branch_id.id),
                                     ('job_id', '=', job_line.upper_position.id)], limit=1)
                                if direct_mng:
                                    employee.write(
                                        {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id})
                    elif employee.id == old_manager_id:
                        job_line = job_line_obj.sudo().search(
                            [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
                             ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
                        if job_line and job_line.upper_position:
                            direct_mng = employee_obj.sudo().search([('company_id', '=', job_line.company_id.id),
                                                                     ('branch_id', '=', job_line.branch_id.id),
                                                                     ('job_id', '=', job_line.upper_position.id)],
                                                                    limit=1)
                            if direct_mng:
                                employee.write(
                                    {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id})

            if old_job_id != res.job_id.id:
                if old_job_id and branch_id and company_id:
                    for employee in job_emp_ids:  # employee_obj.search([('company_id','=',company_id),('branch_id','=',branch_id),('job_id','=',old_job_id)]):
                        if employee.id != res.manager_id.id and res.manager_id:
                            employee.write({'parent_id': res.manager_id.id})
                        elif employee.id == res.manager_id.id or not res.manager_id.id:
                            job_line = job_line_obj.sudo().search(
                                [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
                                 ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
                            if job_line and job_line.upper_position:
                                direct_mng = employee_obj.sudo().search(
                                    [('company_id', '=', job_line.company_id.id),
                                     ('branch_id', '=', job_line.branch_id.id),
                                     ('job_id', '=', job_line.upper_position.id)], limit=1)
                                if direct_mng:
                                    employee.write(
                                        {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id})

            # if approve_manager_id != res.approve_manager.id:
            #     for employee in mng_emp_ids:
            #         if employee.id != approve_manager_id:
            #             if vals.get('approve_manager'):
            #                 # employee.write({'parent_id':vals.get('manager_id')})
            #                 emp = employee_obj.sudo().browse([vals.get('approve_manager')])
            #                 if employee.id != vals.get('approve_manager'):
            #                     employee.write({'manager_job_id': emp.job_id.id, 'parent_id': rec.manager_id.id,
            #                                     'approve_manager': vals.get('approve_manager')})
            #                 else:
            #                     job_line = job_line_obj.sudo().search(
            #                         [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
            #                          ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
            #                     if job_line and job_line.upper_position:
            #                         direct_mng = employee_obj.sudo().search(
            #                             [('company_id', '=', job_line.company_id.id),
            #                              ('branch_id', '=', job_line.branch_id.id),
            #                              ('job_id', '=', job_line.upper_position.id)], limit=1)
            #                         if direct_mng:
            #                             employee.write(
            #                                 {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id,
            #                                  'approve_manager': approve_manager_id.id})
            #             else:
            #                 job_line = job_line_obj.sudo().search(
            #                     [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
            #                      ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
            #                 if job_line and job_line.upper_position:
            #                     direct_mng = employee_obj.sudo().search(
            #                         [('company_id', '=', job_line.company_id.id),
            #                          ('branch_id', '=', job_line.branch_id.id),
            #                          ('job_id', '=', job_line.upper_position.id)], limit=1)
            #                     if direct_mng:
            #                         employee.write(
            #                             {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id,
            #                              'approve_manager': approve_manager_id.id})
            #         elif employee.id == approve_manager_id:
            #             job_line = job_line_obj.sudo().search(
            #                 [('job_id', '=', res.job_id.id), ('company_id', '=', company_id),
            #                  ('branch_id', '=', branch_id), ('department_id', '=', res.id)], limit=1)
            #             if job_line and job_line.upper_position:
            #                 direct_mng = employee_obj.sudo().search([('company_id', '=', job_line.company_id.id),
            #                                                          ('branch_id', '=', job_line.branch_id.id),
            #                                                          ('job_id', '=', job_line.upper_position.id)],
            #                                                         limit=1)
            #                 if direct_mng:
            #                     employee.write(
            #                         {'manager_job_id': job_line.upper_position.id, 'parent_id': direct_mng.id,
            #                          'approve_manager': approve_manager_id.id})


