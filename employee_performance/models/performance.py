# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo import tools
_logger = logging.getLogger(__name__)

class AddEmployees(models.TransientModel):
    _name = 'add.employees'
    _description = 'Generate Performance Evaluation records'

    date_range_id = fields.Many2one('performance.date.range', string='Period', required=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_performance_group_class_rel', 'performance_id', 'employee_id', string='Employees')
    date_start = fields.Date(string="Start Date", related='date_range_id.date_start')
    date_end = fields.Date(string="End Date", related='date_range_id.date_end')

    def compute_sheet(self):
        [data] = self.read()
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate evaluation(s)."))
        # Add 1 day.
        for employee in self.employee_ids:
            performance_id = self.env['employee.performance'].create({
                'employee_id':employee.id,
                'date_range_id':self.date_range_id.id,
            })
            performance_id.onchange_employee_id()
            performance_id.onchange_template_id()
            performance_id.onchange_comp_template_id()

class PerformanceDateRange(models.Model):
    _name = "performance.date.range"
    _description = "Performance Date Range"

    name = fields.Char(required=True,string="Name")
    date_start = fields.Date(string='Start date', required=True)
    date_end = fields.Date(string='End date', required=True)
    mid_from_date = fields.Date(string="Mid From Date", required=True)
    mid_to_date = fields.Date(string="Mid To Date", required=True)
    end_from_date = fields.Date(string="End From Date", required=True)
    end_to_date = fields.Date(string="End To Date", required=True)
    

class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'HR Job'

    template_id = fields.Many2one('performance.template', string='Template ID')
    comp_template_id = fields.Many2one('competencies.template', string='Competencies Template')

class EmployeePerformance(models.Model):
    _name = 'employee.performance'
    _description = 'Employee Performance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    name = fields.Char(string='Name')
    company_id = fields.Many2one(string="Company", comodel_name='res.company')
    branch_id = fields.Many2one('res.branch', string='Branch', domain="[('company_id', '=', company_id)]")
    employee_id = fields.Many2one('hr.employee', required=True)
    job_id = fields.Many2one('hr.job', string='Position')
    template_id = fields.Many2one('performance.template', string='Key Performance Template')
    comp_template_id = fields.Many2one('competencies.template', string='Competencies Template')
    competencies_ids = fields.One2many('key.competencies', 'performance_id', string='Key Performance')
    key_performance_ids = fields.One2many('key.performance', 'performance_id', string='COMPETENCIES', store=True)
    date_range_id = fields.Many2one('performance.date.range', string='Period')
    date_start = fields.Date(string="Start Date", related='date_range_id.date_start', store=True)
    date_end = fields.Date(string="End Date", related='date_range_id.date_end', store=True)
    mid_from_date = fields.Date(string="Mid From Date",related='date_range_id.mid_from_date', store=True)
    mid_to_date = fields.Date(string="Mid To Date",related='date_range_id.mid_to_date', store=True)
    end_from_date = fields.Date(string="End From Date",related='date_range_id.end_from_date', store=True)
    end_to_date = fields.Date(string="End To Date",related='date_range_id.end_to_date', store=True)
    state = fields.Selection([('draft', 'Draft'), ('sent_to_employee', 'Sent To Employee'),
                            ('acknowledge', 'Acknowledge'), ('mid_year_self_assessment', 'Mid Year Self Assessment'),
                            ('mid_year_manager_approve', 'Mid Year Manager Approve'),
                            ('mid_year_hr_approve', 'Mid Year HR Approve'), ('year_end_self_assessment', 'Year End Self Assessment'),
                            ('year_end_manager_approve', 'Year End Manager Approve'),
                            ('sent_to_manager', 'Sent To Manager'), ('year_end_hr_approve', 'Year End HR Approve'), ('cancel', 'Cancel')],
                             string='Status', track_visibility='onchange', required=True,
                             copy=False, default='draft')
    planning = fields.Char(string="PLANNING AND ORGANIZING:",default="Draws a detailed and comprehensive plan before starting an important task/projec Develops clear and realistic plans follows up and revisits status as task proceeds Is able to manage multiple competing & important activities effectively", readonly=True)
    planning_text = fields.Text(string='Comments')
    planning_score = fields.Float(string='Score')
    leadership = fields.Char(string="Leadership",default="Works co-operatively & effectively with team members within and outside the group Takes ownership of job, situations & results Is able to establish & share a clear vision and influence team to achieve it Is able to coach, mentor, guide & motivate own & extended teams to achieve results", readonly=True)
    leadership_text = fields.Text(string='Comments')
    leadership_score = fields.Float(string='Score')

    accountability = fields.Char(string="ACCOUNTABILITY",default="Accepts responsibility for own actions & decisions & demonstrates commitment to accomplish work in an ethical, efficient and cost-effective manner Establishes priorities, monitors progress and makes effective recommendation", readonly=True)
    accountability_text = fields.Text(string='Comments')
    accountability_score = fields.Float(string='Score')

    innovation = fields.Char(string="INNOVATION",default="Anticipates organizational needs, identifies and acts upon new opportunities to enhance results / minimize problems Offers creative suggestions for improvement & develops new approaches to work", readonly=True)
    innovation_text = fields.Text(string='Comments')
    innovation_score = fields.Float(string='Score')

    collaboration = fields.Char(string="COLLABORATION",default="Builds rapport and goodwill with Principals/Vendors/Customers/Internal teams Acts beyond required or expected effort and proactively originates results Is resourceful and develops healthy inter department relationships to ensure work effectiveness", readonly=True)
    collaboration_text = fields.Text(string='Comments')
    collaboration_score = fields.Float(string='Score')

    job_skill = fields.Float(string='Job Knowledge')
    handle_skill = fields.Float(string='Work handling skills')
    learn_skill = fields.Float(string='Learn new skill')
    one_time = fields.Float(string='Completion on time')
    pressure = fields.Float(string='handling work pressure')
    portfolio = fields.Float(string='handling new portfolio')
    achievement = fields.Text(string='Achievement')
    improvement = fields.Text(string='improvement')
    development = fields.Text(string='development')
    deadline_end = fields.Boolean(string='development')
    deadline = fields.Date(string='Deadline')
    mid_send = fields.Boolean(string='Mid',default=False)
    final_send = fields.Boolean(string='Final',default=False)

    competency_score = fields.Float(string='Competency Score', digits='PMS Decimal Precision', compute='_compute_competency_score', store=True)
    kpi = fields.Float(string='KPI', digits='PMS Decimal Precision', compute='_compute_employee_kpi', store=True)
    mid_competency_score = fields.Float(string='Competency Score', digits='PMS Decimal Precision', compute='_compute_competency_score', store=True)
    mid_kpi = fields.Float(string='KPI', digits='PMS Decimal Precision', compute='_compute_employee_kpi', store=True)
    final_rating = fields.Float(string='End Final Rating', digits='PMS Decimal Precision', compute='_compute_final_rating', store=True)
    mid_rating = fields.Float(string='Mid Final Rating', digits='PMS Decimal Precision', compute='_compute_mid_rating', store=True)
    # dotted_line_manager_id = fields.Many2one('hr.employee', related='employee_id.dotted_line_manager_id', store=True, string='Dotted Line Manager',
    #                              readonly=True)
    
    pms_create_date = fields.Date(string='Create Date', default=fields.Date.today())
    is_submitted = fields.Boolean(string='Is Submitted?', default=False)
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        self.job_id = self.employee_id.job_id.id
        
    @api.depends('competencies_ids.score', 'state')
    def _compute_competency_score(self):
        for rec in self:
#             today_date = fields.Date.today()
            score = compt_score = 0
            rec.competency_score = 0
            rec.mid_competency_score = 0 
            if rec.competencies_ids:
                for line in rec.competencies_ids:
                    score += line.score
            if len(rec.competencies_ids) > 0:
                compt_score = score / len(rec.competencies_ids)  
#             if today_date >= rec.mid_from_date and today_date <= rec.mid_to_date:  
#                 rec.mid_competency_score = compt_score
#             elif today_date >= rec.end_from_date and today_date <= rec.end_to_date:
#                 rec.competency_score = compt_score             
            rec.mid_competency_score = compt_score
            if rec.state in ['year_end_self_assessment', 'year_end_manager_approve', 'year_end_dotted_manager_approve', 'sent_to_manager', 'year_end_hr_approve']: 
                rec.competency_score = compt_score    
                
    @api.depends('key_performance_ids.mgr_calculate', 'state')
    def _compute_employee_kpi(self):
        for rec in self:
#             today_date = fields.Date.today()
            rec.kpi = 0
            rec.mid_kpi = 0
            if rec.key_performance_ids:
#                 if today_date >= rec.mid_from_date and today_date <= rec.mid_to_date: 
#                     rec.mid_kpi = sum(x.mgr_calculate for x in rec.key_performance_ids) 
#                 elif today_date >= rec.end_from_date and today_date <= rec.end_to_date:
#                     rec.kpi = sum(x.mgr_calculate for x in rec.key_performance_ids)
                rec.mid_kpi = sum(x.mgr_calculate for x in rec.key_performance_ids) 
                if rec.state in ['year_end_self_assessment', 'year_end_manager_approve', 'year_end_dotted_manager_approve', 'sent_to_manager', 'year_end_hr_approve']: 
                    rec.kpi = sum(x.mgr_calculate for x in rec.key_performance_ids)
                
    @api.depends('mid_kpi', 'mid_competency_score')
    def _compute_mid_rating(self):
        for rec in self:
            rec.mid_rating = 0
#             today_date = fields.Date.today()
#             if today_date >= rec.mid_from_date and today_date <= rec.mid_to_date:
#             if rec.state in ['mid_year_self_assessment', 'mid_year_manager_approve', 'mid_year_dotted_manager_approve', 'mid_year_hr_approve']:  
            salary_struct = rec.employee_id.contract_id.structure_type_id
            if salary_struct:
                # if rec.employee_id.contract_id.struct_id.is_staff:
                #     rec.mid_rating = (rec.mid_kpi * 0.8) + (rec.mid_competency_score * 0.2)
                # elif rec.employee_id.contract_id.struct_id.is_manager:
                rec.mid_rating = (rec.mid_kpi * 0.6) + (rec.mid_competency_score * 0.4)
                # elif rec.employee_id.contract_id.struct_id.is_management:
                #     rec.mid_rating = (rec.mid_kpi * 0.4) + (rec.mid_competency_score * 0.6)
                        
    @api.depends('kpi', 'competency_score')
    def _compute_final_rating(self):
        for rec in self:
            rec.final_rating = 0
#             today_date = fields.Date.today()
#             if today_date >= rec.end_from_date and today_date <= rec.end_to_date:
            if rec.state in ['year_end_self_assessment', 'year_end_manager_approve', 'year_end_dotted_manager_approve', 'sent_to_manager', 'year_end_hr_approve']: 
                salary_struct = rec.employee_id.contract_id.structure_type_id
                if salary_struct:
                    # if rec.employee_id.contract_id.structure_type_id.is_staff:
                    #     rec.final_rating = (rec.kpi * 0.8) + (rec.competency_score * 0.2)
                    # elif rec.employee_id.contract_id.struct_id.is_manager:
                    rec.final_rating = (rec.kpi * 0.6) + (rec.competency_score * 0.4)
                    # elif rec.employee_id.contract_id.struct_id.is_management:
                    #     rec.final_rating = (rec.kpi * 0.4) + (rec.competency_score * 0.6)
    
    @api.constrains('key_performance_ids')
    def _constrains_key_performance_ids(self):
        total_weightage = 0
        if self.key_performance_ids:
            for line in self.key_performance_ids:
                total_weightage = total_weightage + line.weightage
        if total_weightage != 100:
            raise ValidationError("Total weightage(%) must be 100!")
        
    @api.constrains('employee_id', 'date_range_id', 'template_id', 'comp_template_id')
    def _check_duplicate_pms(self):
        same_pms = self.env['employee.performance'].sudo().search([('employee_id', '=', self.employee_id.id),
                                                                   ('date_range_id', '=', self.date_range_id.id),
                                                                   ('template_id', '=', self.template_id.id),
                                                                   ('comp_template_id', '=', self.comp_template_id.id),
                                                                   ('id', '!=', self.id)])
        if same_pms:
            raise ValidationError(_("%s performance evaluation is already created for %s." ) % (self.employee_id.name, self.date_range_id.name))
    
    @api.model
    def create(self, vals):
        # if vals.get('name', _('New')) == _('New'):
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('employee.performance')
        # if vals.get('employee_id'):
        #     employee_id = self.env['hr.employee'].sudo().browse(vals['employee_id'])
        #     period_id = vals['date_range_id']
        #     period = self.env['performance.date.range'].sudo().browse(period_id)
        #     one_signal_values = {'employee_id': employee_id.id,
        #                         'contents': _('Performance Evulation created for %s') % (period.name),
        #                         'headings': _('WB B2B : Performance Evulation Created')}
        #     self.env['one.signal.notification.message'].create(one_signal_values)
        if vals.get('employee_id'):
            employee_id = self.env['hr.employee'].sudo().browse(vals['employee_id'])
            period_id = vals['date_range_id']
            period = self.env['performance.date.range'].sudo().browse(period_id)
            if period:
                content = 'Performance Evaluation created for %s' % (period.name)
            message_title = 'MAEX : Performance Evaluation Created'
            if employee_id.device_token and period:
                firebase_values = {'employee_id': employee_id.id,
                                   'contents': _('Performance Evaluation created for %s') % (period.name),
                                   'headings': _('MAEX : Performance Evaluation Created')}
                self.env['firebase.notification.message'].create(firebase_values)
                employee_id.send_noti([self.employee_id.device_token], content, message_title)
        return super(EmployeePerformance, self).create(vals)

    def action_cancel(self):
        self.write({'state':'cancel'})

    def action_draft(self):
        self.write({'state':'draft'})
    
    def _mid_generate_entries(self):
        for move in self.search([('mid_from_date','=',datetime.today()),('mid_send','=',False)]):
            move.write({'mid_send':True})

            content = 'Performance Evaluation for %s %s-%s' % (move.employee_id.name, move.mid_from_date, move.mid_to_date)
            message_title = 'MAEX : Performance Evaluation for Mid Period'
            if move.employee_id.device_token:
                firebase_values = {'employee_id': move.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation Created')}
                self.env['firebase.notification.message'].create(firebase_values)
                move.employee_id.send_noti([move.employee_id.device_token], content, message_title)
    
    def _final_generate_entries(self):
        for move in self.search([('end_from_date','=',datetime.today()),('final_send','=',False)]):
            # move.write({'final_send':True})
            # one_signal_values = {'employee_id': move.employee_id.id,
            #                          'contents': _('Performance Evulation for %s %s-%s') % (move.employee_id.name,move.end_from_date,move.end_to_date),
            #                          'headings': _('WB B2B : Performance Evulation for Final Period')}
            # self.env['one.signal.notification.message'].create(one_signal_values)
            content = "Performance Evaluation for %s %s-%s" % move.employee_id.name, move.end_from_date, move.end_to_date
            message_title = 'MAEX : Performance Evaluation for Final Period'
            if move.employee_id.device_token:
                firebase_values = {'employee_id': move.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation for Final Period')}
                self.env['firebase.notification.message'].create(firebase_values)
                move.employee_id.send_noti([move.employee_id.device_token], content, message_title)
            
    def action_sent_employee(self):
        self.write({'state':'sent_to_employee'})
        # one_signal_values = {'employee_id': self.employee_id.id,
        #                     'contents': _('Your Performance Evulation for %s') % (self.date_range_id.name),
        #                     'headings': _('WB B2B : Performance Evulation')}
        # self.env['one.signal.notification.message'].create(one_signal_values)
        content = "Your Performance Evaluation for %s'" % self.date_range_id.name
        message_title = 'MAEX : Performance Evaluation'
        if self.employee_id.device_token:
            firebase_values = {'employee_id': self.employee_id.id,
                               'contents': content,
                               'headings': _('MAEX : Performance Evaluation')}
            self.env['firebase.notification.message'].create(firebase_values)
            self.employee_id.send_noti([self.employee_id], content, message_title)
                
    def action_acknowledge(self):
        self.write({'state':'acknowledge'})
        # if self.employee_id.approve_manager:
        #     one_signal_values = {'employee_id': self.employee_id.approve_manager.id,
        #                         'contents': _('%s acknowledged performance evulation for %s') % (self.employee_id.name,self.date_range_id.name),
        #                         'headings': _('WB B2B : Performance Evulation')}
        #     self.env['one.signal.notification.message'].create(one_signal_values)
        content = ("%s acknowledged performance evaluation for %s" % (self.employee_id.name, self.date_range_id.name))
        message_title = 'MAEX : Performance Evaluation'
        if self.employee_id.device_token:
            registration_ids = []
            if self.employee_id.device_token:
                registration_ids.append(self.employee_id.device_token)
                firebase_values = {'employee_id': self.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation')}
                self.env['firebase.notification.message'].create(firebase_values)
        # if self.employee_id.dotted_line_manager_id:
        #     firebase_values = {'employee_id': self.employee_id.dotted_line_manager_id.id,
        #                        'contents': content,
        #                        'headings': _('MAEX : Performance Evaluation')}
        #     self.env['firebase.notification.message'].create(firebase_values)
        #     # registration_ids.append(self.employee_id.dotted_line_manager_id.device_token)
        #     self.employee_id.send_noti(registration_ids, content, message_title)

    def action_mid_year_self_assessment(self):
        self.write({'state': 'mid_year_self_assessment'})
        if self.employee_id.approve_manager:
            # one_signal_values = {'employee_id': self.employee_id.approve_manager.id,
            #                     'contents': _('%s submit mid-year self assessment for %s') % (self.employee_id.name,self.date_range_id.name),
            #                     'headings': _('WB B2B : Performance Evulation')}
            # self.env['one.signal.notification.message'].create(one_signal_values)
            content = ("%s submit mid-year self assessment for %s" % (self.employee_id.name, self.date_range_id.name))
            message_title = 'MAEX : Performance Evaluation'
            if self.employee_id.device_token:
                firebase_values = {'employee_id': self.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation')}
                self.env['firebase.notification.message'].create(firebase_values)
                self.employee_id.send_noti([self.employee_id.device_token], content, message_title)
    
    def action_mid_year_manager_approve(self):
        self.write({'state': 'mid_year_manager_approve'})
        if self.employee_id.approve_manager:
            # one_signal_values = {'employee_id': self.employee_id.branch_id.hr_manager_id.id,
            #                     'contents': _('Dotted Manager approved performance evulation for %s') % (self.employee_id.name),
            #                     'headings': _('WB B2B : Performance Evulation')}
            # self.env['one.signal.notification.message'].create(one_signal_values)
            content = "Dotted Manager approved performance evaluation for %s" % self.employee_id.name
            message_title = 'MAEX : Performance Evaluation'
            if self.employee_id.device_token:
                firebase_values = {'employee_id': self.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation')}
                self.env['firebase.notification.message'].create(firebase_values)
                self.employee_id.send_noti([self.employee_id.device_token], content, message_title)
    
    def action_mid_year_hr_approve(self):
        self.write({'state': 'mid_year_hr_approve'})
    
    def action_year_end_self_assessment(self):
        self.write({'state': 'year_end_self_assessment'})
        if self.employee_id.approve_manager:
            # one_signal_values = {'employee_id': self.employee_id.approve_manager.id,
            #                     'contents': _('%s submit year end self assessment for %s') % (self.employee_id.name,self.date_range_id.name),
            #                     'headings': _('WB B2B : Performance Evulation')}
            # self.env['one.signal.notification.message'].create(one_signal_values)
            content = ("%s submit year end self assessment for %s" % (self.employee_id.name, self.date_range_id.name))
            message_title = 'MAEX : Performance Evaluation'
            if self.employee_id.device_token:
                firebase_values = {'employee_id': self.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation')}
                self.env['firebase.notification.message'].create(firebase_values)
                self.employee_id.send_noti([self.employee_id.device_token], content, message_title)

    def action_year_end_manager_approve(self):
        self.write({'state': 'year_end_manager_approve'})
        if self.employee_id.approve_manager:
            # one_signal_values = {'employee_id': self.employee_id.dotted_line_manager_id.id,
            #                     'contents': _('Manager approved performance evulation for %s') % (self.employee_id.name),
            #                     'headings': _('WB B2B : Performance Evulation')}
            # self.env['one.signal.notification.message'].create(one_signal_values)
            content = "Manager approved performance evaluation for %s" % self.employee_id.name
            message_title = 'MAEX : Performance Evaluation'
            if self.employee_id.device_token:
                firebase_values = {'employee_id': self.employee_id.id,
                                   'contents': content,
                                   'headings': _('MAEX : Performance Evaluation')}
                self.env['firebase.notification.message'].create(firebase_values)
                self.employee_id.send_noti([self.employee_id.device_token], content, message_title)

    def action_year_end_hr_approve(self):
        self.write({'state': 'year_end_hr_approve'})
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.template_id = self.employee_id.job_id.template_id.id
            self.comp_template_id = self.employee_id.job_id.comp_template_id.id

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            key_lines = []
            key_performance_ids = self.template_id.key_performance_ids
            for line in key_performance_ids:
                key_lines.append(line.copy())
            self.key_performance_ids = [(6, 0, [x.id for x in key_lines])]

    @api.onchange('comp_template_id')
    def onchange_comp_template_id(self):
        if self.comp_template_id:
            key_lines = []
            competencies_ids = self.comp_template_id.competencies_ids
            for line in competencies_ids:
                key_lines.append(line.copy())
            self.competencies_ids = [(6, 0, [x.id for x in key_lines])]

    def write(self, vals):        
        res = super(EmployeePerformance, self).write(vals)
        return res

    def approve_mid_year_dotted_manager(self, force_approve=False):
        domain = []
        if not force_approve:
            domain = [('state', '=', 'draft')]
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]

        mid_manager = self.search(domain)
        for mid_manager in mid_manager:
            if force_approve:
                mid_manager.state = 'mid_year_dotted_manager_approve'
            else:
                mid_manager.state = 'mid_year_dotted_manager_approve'
                
    def mid_hr_approve_manager(self):
        domain = []
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]
        hr_manager = self.search(domain)
        for hr_manager in hr_manager:
            hr_manager.state = 'mid_year_hr_approve'
            
    def approve_year_end_dotted_manager(self):
        domain = []
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]
        year_dotted_manager = self.search(domain)
        for dotted_manager in year_dotted_manager:
            dotted_manager.state = 'year_end_dotted_manager_approve'
    
    def act_year_end_hr_approve(self):
        domain = []
        if self._context.get('active_ids'):
            domain += [('id', 'in', self._context.get('active_ids'))]
        year_hr_approve = self.search(domain)
        for hr_approve in year_hr_approve:
            hr_approve.state = 'year_end_hr_approve'
                                
class PerformanceTemplate(models.Model):
    _name = 'performance.template'
    _description = 'Employee Performance Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    company_id = fields.Many2one(string="Current Company", comodel_name='res.company', default=_get_current_company)
    name = fields.Char('Name', required=True)
    key_performance_ids = fields.One2many('key.performance', 'key_id', string='Key Performance')
    job_id = fields.Many2one('hr.job', string='Position')
    
class KeyPerformance(models.Model):
    _name = 'key.performance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Key Performance'

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    company_id = fields.Many2one(string="Current Company", comodel_name='res.company', default=_get_current_company)
    name = fields.Char('KEY PERFORMANCE AREAS', required=True)
    description = fields.Char('Description')
    hint = fields.Char('Hint')
    weightage = fields.Integer('WEIGHTAGE(%)')
    key_id = fields.Many2one('performance.template', 'Template',  copy=False)
    employee_rate = fields.Integer('Employee Self-Assessment')
    employee_remark = fields.Char('Employee Remarks')
    manager_rate = fields.Integer('Manager Rating', default=0)
    mgr_calculate = fields.Float('Mgr Calculate', digits='PMS Decimal Precision', compute="_compute_mgr")
    hidden_rate = fields.Float('Calculate', digits='PMS Decimal Precision', compute="_compute_hidden")
    manager_remark = fields.Char('Manager Remarks')
    performance_id = fields.Many2one('employee.performance', 'Performance Evaluation')
    comment = fields.Char(string="Comment")
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([('draft', 'Draft'), ('sent_to_employee', 'Sent To Employee'),
                            ('acknowledge', 'Acknowledge'), ('mid_year_self_assessment', 'Mid Year Self Assessment'),
                            ('mid_year_manager_approve', 'Mid Year Manager Approve'), ('mid_year_dotted_manager_approve', 'Mid Year Dotted Manager Approve'),
                            ('mid_year_hr_approve', 'Mid Year HR Approve'), ('year_end_self_assessment', 'Year End Self Assessment'),
                            ('year_end_manager_approve', 'Year End Manager Approve'), ('year_end_dotted_manager_approve', 'Year End Dotted Manager Approve'),
                            ('sent_to_manager', 'Sent To Manager'), ('year_end_hr_approve', 'Year End HR Approve'), ('cancel', 'Cancel')],
                             'Status', track_visibility='onchange', required=True,
                             copy=False, default='draft', related='performance_id.state')
    employee_id = fields.Many2one('hr.employee', 'Employee', related='performance_id.employee_id')

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    
    @api.depends('weightage', 'manager_rate')
    def _compute_mgr(self):
        for line in self:
            if line.manager_rate > 0:
                mgr = (line.weightage * line.manager_rate)/100         
                line.update({                
                    'mgr_calculate': mgr,
                })
            else:
                line.update({                
                    'mgr_calculate': 0.00,
                })

        
    @api.onchange('manager_rate')
    def change_manager_rate(self):
        if self.manager_rate > 5 or self.manager_rate < 1:
            raise ValidationError(_('Final Rating Value must be between 1 and 5.')) 
            
    @api.depends('weightage', 'employee_rate')
    def _compute_hidden(self):
        for hide in self:
            weight = hide.weightage 
            hidden = (hide.weightage * hide.employee_rate)/100         
            hide.update({                
                'hidden_rate': hidden,
            })
    
class CompetenciesTemplate(models.Model):
    _name = 'competencies.template'
    _description = 'Employee Competencies Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    company_id = fields.Many2one(string="Current Company", comodel_name='res.company', default=_get_current_company)
    name = fields.Char('Name', required=True)
    competencies_ids = fields.One2many('key.competencies', 'key_id', string='Key Performance')

class KeyCompetencies(models.Model):
    _name = 'key.competencies'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Key Competencies'

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    company_id = fields.Many2one(string="Current Company", comodel_name='res.company', default=_get_current_company)
    name = fields.Char('KEY PERFORMANCE AREAS', required=True)
    description = fields.Char('Description')
    key_id = fields.Many2one('competencies.template', 'Template Name', copy=False)
    performance_id = fields.Many2one('employee.performance', 'Performance Evaluation')
    comment = fields.Char(string="Comment")
    sequence = fields.Integer(string='Sequence', default=10)
    score = fields.Float('Score')
    employee_id = fields.Many2one('hr.employee', 'Employee', related='performance_id.employee_id')

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    state = fields.Selection([('draft', 'Draft'), ('sent_to_employee', 'Sent To Employee'),('sent_to_manager', 'Sent To Manager'), ('done', 'Done'),('cancel', 'Cancel')],
                             'Status', track_visibility='onchange', copy=False, related='performance_id.state')



class ReportKeyPerformance(models.Model):
    _name = "report.key.performance"
    _description = "Performance"
    _auto = False

    create_date = fields.Datetime('Creation Date', readonly=True)
    performance_id = fields.Many2one('employee.performance', 'Performance', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    company_id = fields.Many2one('res.company', 'Company')
    branch_id = fields.Many2one('res.branch', 'Branch')
    department_id = fields.Many2one('hr.department', 'Department')
    job_id = fields.Many2one('hr.job', 'Position')
    manager_id = fields.Many2one('hr.employee', 'Manager')
    date_range_id = fields.Many2one('performance.date.range', 'Period')
    weightage = fields.Float('Weightage')
    employee_rate = fields.Float(
        'Employee Rate', required=True)
    manager_rate = fields.Float(
        'Manager Rate', required=True)
    template_id = fields.Many2one('performance.template', 'Evaluation Template')
    key_performance_id = fields.Many2one('key.performance', 'Key performance')

    def _select(self):
        return """
            SELECT
                performance.id AS id,                
                performance.id AS key_performance_id,                
                ep.id AS performance_id,
                employee.id AS employee_id,  
                company.id AS company_id,
                branch.id AS branch_id,
                department.id AS department_id,
                job.id AS job_id,
                manager.id AS manager_id,
                dr.id AS date_range_id,                             
                pt.id AS template_id,                             
                performance.weightage AS weightage,
                performance.employee_rate AS employee_rate,
                performance.manager_rate AS manager_rate,
                ep.create_date AS create_date
            """

    def _from(self):
        return """
            FROM
                employee_performance ep
                JOIN key_performance performance ON ep.id = performance.performance_id
                JOIN performance_date_range dr ON dr.id = ep.date_range_id
                JOIN hr_employee employee ON ep.employee_id = employee.id
                JOIN res_company company ON employee.company_id = company.id
                JOIN res_branch branch ON employee.branch_id = branch.id
                JOIN hr_department department ON employee.department_id = department.id
                JOIN hr_job job ON employee.job_id = job.id
                JOIN hr_employee manager ON employee.parent_id = manager.id
                JOIN performance_template pt ON pt.id = ep.template_id
            """

    def _group_by(self):
        return """
            GROUP BY
                performance.id,                            
                employee.id,
                company.id,
                branch.id,
                department.id,
                job.id,
                manager.id,
                dr.id,
                pt.id,
                ep.create_date,
                ep.id
            """

    def _order_by(self):
        return """
            ORDER BY
                employee_id
            """

    def _where(self):
        return """
            WHERE
                performance.display_type = 'False' AND performance.id IS NOT NULL
            """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            "CREATE or REPLACE VIEW %s as (%s %s %s %s)" % (
                self._table, self._select(), self._from(),self._group_by(), self._order_by()
            )
        )

class ReportCompetencies(models.Model):
    _name = "report.competencies"
    _description = "Competencies Report"
    _auto = False

    create_date = fields.Datetime('Creation Date', readonly=True)
    performance_id = fields.Many2one('employee.performance', 'Performance', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    date_range_id = fields.Many2one('performance.date.range', 'Period')
    employee_rate = fields.Float(
        'Score', required=True)
    template_id = fields.Many2one('competencies.template', 'Evaluation Template')
    key_performance_id = fields.Many2one('key.competencies', 'Competencies')

    def _select(self):
        return """
            SELECT
                performance.id AS id,   
                performance.id AS key_performance_id,                             
                ep.id AS performance_id,
                employee.id AS employee_id,  
                dr.id AS date_range_id,                             
                pt.id AS template_id,                             
                performance.score AS employee_rate,
                ep.create_date AS create_date
            """

    def _from(self):
        return """
            FROM
                employee_performance ep
                JOIN key_competencies performance ON ep.id = performance.performance_id
                JOIN performance_date_range dr ON dr.id = ep.date_range_id
                JOIN hr_employee employee ON ep.employee_id = employee.id
                JOIN competencies_template pt ON pt.id = ep.comp_template_id
            """

    def _group_by(self):
        return """
            GROUP BY
                performance.id,                            
                employee.id,
                dr.id,
                pt.id,
                ep.create_date,
                ep.id
            """

    def _order_by(self):
        return """
            ORDER BY
                employee_id
            """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            "CREATE or REPLACE VIEW %s as (%s %s %s %s)" % (
                self._table, self._select(), self._from(), self._group_by(), self._order_by()
            )
        )