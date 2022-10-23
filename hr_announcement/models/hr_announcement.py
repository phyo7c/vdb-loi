# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAnnouncement(models.Model):
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Code No:', help="Sequence Number of the Announcement")
    announcement_company_id = fields.Many2one('res.company', string='Announcement Company')
    announcement_reason = fields.Text(string='Title', states={'draft': [('readonly', False)]}, required=True,
                                      readonly=True, help="Announcement Subject")
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
                              ('approved', 'Approved'), ('rejected', 'Refused'), ('expired', 'Expired')],
                             string='Status',  default='draft',
                             track_visibility='always')
    requested_date = fields.Date(string='Requested Date', default=datetime.now().strftime('%Y-%m-%d'),
                                 help="Create Date of Record")
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
                                     string="Attachment", help='You can attach the copy of your Letter')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id, readonly=True, help="Login user Company")
    branch_ids = fields.Many2many('res.branch', string='Branch', domain="[('company_id', '=', announcement_company_id)]")
    is_announcement = fields.Boolean(string='Is general Announcement?', help="To set Announcement as general announcement")
    announcement_type = fields.Selection([('employee', 'By Employee'), ('department', 'By Department'), ('job_grade', 'By Job Grade')])
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_announcements', 'announcement', 'employee',
                                    string='Employees', domain="[('company_id', '=', announcement_company_id)]",
                                    help="Employee's which want to see this announcement")
    department_ids = fields.Many2many('hr.department', 'hr_department_announcements', 'announcement', 'department',
                                      string='Departments', domain="[('company_id', '=', announcement_company_id)]",
                                      help="Department's which want to see this announcement")
    # position_ids = fields.Many2many('hr.job', 'hr_job_position_announcements', 'announcement', 'job_position',
    #                                 string='Job Positions',help="Job Position's which want to see this announcement")
    job_grade_ids = fields.Many2many('job.grade', string='Job Grade',help="Job Grade's which want to see this announcement")
    announcement = fields.Html(string='Letter', states={'draft': [('readonly', False)]}, readonly=True, help="Announcement Content")
    date_start = fields.Date(string='Start Date', default=fields.Date.today(), required=True, help="Start date of announcement want to see")
    date_end = fields.Date(string='End Date', default=fields.Date.today(), required=True, help="End date of announcement want too see")
    job_id = fields.Many2one('hr.job', string='Job Position', domain="[('company_id', '=', announcement_company_id)]")
    
    def reject(self):
        self.state = 'rejected'

    def approve(self):
        self.state = 'approved'
        registration_ids = []
        domain = [('user_id', '=', self.create_uid.id)]
        if self.announcement_company_id:
            domain = [('company_id', '=', self.announcement_company_id.id)]
            if self.branch_ids:
                domain += [('branch_id', 'in', self.branch_ids.ids)]
            else:
                branches = self.env['res.branch'].sudo().search([('company_id', '=', self.announcement_company_id.id)])
                domain += [('branch_id', 'in', branches.ids)]
            
            if self.announcement_type:
                if self.announcement_type == 'employee' and self.employee_ids:
                    domain += [('id', 'in', self.employee_ids.ids)]
                if self.announcement_type == 'department' and self.department_ids:
                    domain += [('department_id', 'in', self.department_ids.ids)]
                if self.announcement_type == 'job_grade' and self.job_grade_ids:
                    domain += [('contract_id.job_grade_id', 'in', self.job_grade_ids.ids)]
            
        if self.is_announcement == True:
            all_companies = self.env['res.company'].sudo().search([])
            domain = [('company_id','in', all_companies.ids)]
            
        for emp_id in self.env['hr.employee'].sudo().search(domain):
            one_signal_values = {'employee_id': emp_id.id,
                                'contents': _('Announcement: %s .') % self.announcement_reason,
                                'headings': _('WB B2B : Announcement %s .') % self.announcement,
                                'message_type': 'announcement',}
                                        
            #self.env['one.signal.notification.message'].create(one_signal_values)
            content = 'Announcement %s ' % self.announcement_reason
            message_title = 'MAEX : Announcement %s' % self.announcement
            firebase_values = {'employee_id': emp_id.id,
                               'contents': content,
                               'headings': message_title}
            self.env['firebase.notification.message'].create(firebase_values)
            if emp_id.device_token:
                self.env['firebase.notification.message'].create(firebase_values)
                registration_ids.append(emp_id.device_token)
            if len(registration_ids) > 0:
                self.env['hr.employee'].send_noti(registration_ids, content, message_title)
    def sent(self):
        self.state = 'to_approve'
        registration_ids = []
        # for emp_id in self.env['hr.employee'].sudo().search([('id', '=', self.announcement_company_id.managing_director_id.id)]):
            # one_signal_values = {'employee_id': emp_id.id,
            #                     'contents': _('To Approve Announcement %s') % self.name,
            #                     'headings': _('WB B2B : APPROVAL ANNOUNCEMENT'),
            #                     'message_type': 'announcement',}
            #
            # self.env['one.signal.notification.message'].create(one_signal_values)
            # content = 'To Approve Announcement %s ' % self.name
            # message_title = 'AKT : APPROVAL ANNOUNCEMENT'
            # if emp_id.device_token:
            #     firebase_values = {'employee_id': emp_id.id,
            #                        'contents': content,
            #                        'headings': _('AKT : APPROVAL ANNOUNCEMENT')}
            #     self.env['firebase.notification.message'].create(firebase_values)
            #     registration_ids.append(emp_id.device_token)
                #emp_id.send_noti([emp_id.device_token], content, message_title)
        if len(registration_ids) > 0:

            self.env['hr.employee'].send_noti(registration_ids, content, message_title)

    @api.constrains('date_start', 'date_end')
    def validation(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be less than End Date")

    @api.model
    def create(self, vals):
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('hr.announcement.general')
        else:
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('hr.announcement')
        return super(HrAnnouncement, self).create(vals)

        # domain = []
        # if res.announcement_company_id:
        #     domain = [('company_id','=',res.announcement_company_id.id)]
        #     if res.branch_ids:
        #         domain += [('branch_id', 'in', res.branch_ids.ids)]
        #     else:
        #         branches = self.env['res.branch'].sudo().search([('company_id', '=', res.announcement_company_id.id)])
        #         domain += [('branch_id','in', branches.ids)]
            
        #     if res.announcement_type:
        #         if res.announcement_type == 'employee' and res.employee_ids:
        #             domain += [('id', 'in', res.employee_ids.ids)]
        #         if res.announcement_type == 'department' and res.department_ids:
        #             domain += [('department_id', 'in', res.department_ids.ids)]
        #         if res.announcement_type == 'job_grade' and res.job_grade_ids:
        #             domain += [('contract_id.job_grade_id', 'in', res.job_grade_ids.ids)]
                
        #     for emp_id in self.env['hr.employee'].sudo().search(domain):
        #         one_signal_values = {'employee_id': emp_id.id,
        #                                  'contents': _('Announcement: %s .') % res.announcement_reason,
        #                                  'headings': _('WB B2B : Announcement %s .') % res.announcement,
        #                                  'message_type': 'announcement',}
                
        #         self.env['one.signal.notification.message'].create(one_signal_values)

        # if res.is_announcement == True:
        #     all_companies = self.env['res.company'].sudo().search([])
        #     domain = [('company_id','in', all_companies.ids)]
        #     # branches = self.env['res.branch'].sudo().search([('company_id', 'in', all_companies.ids)])
        #     # domain += [('branch_id','in', branches.ids)]
            
        #     for emp_id in self.env['hr.employee'].sudo().search(domain):
        #         one_signal_values = {'employee_id': emp_id.id,
        #                                  'contents': _('Announcement: %s .') % res.announcement_reason,
        #                                  'headings': _('WB B2B : Announcement %s .') % res.announcement,
        #                                  'message_type': 'announcement',}
                                         
        #         self.env['one.signal.notification.message'].create(one_signal_values)

    def get_expiry_state(self):
        """
        Function is used for Expiring Announcement based on expiry date
        it activate from the crone job.

        """
        now = datetime.now()
        now_date = now.date()
        ann_obj = self.search([('state', '!=', 'rejected')])
        for recd in ann_obj:
            if recd.date_end < now_date:
                recd.write({
                    'state': 'expired'
                })
