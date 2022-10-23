from odoo import fields, models
import code


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
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
        
    fingerprint_id = fields.Char(string='Fingerprint ID', default=lambda self: self._get_fingerprint_id())
    barcode = fields.Char(string="Badge ID", groups="hr.group_hr_user", default=lambda self: self._get_fingerprint_id(), copy=False)
    pin = fields.Char(string="PIN", groups="hr.group_hr_user", default=lambda self: self._get_fingerprint_id(), copy=False)
    
    # no_need_attendance = fields.Boolean('No need attendance', default=False, copy=False)
    
    _sql_constraints = [
        ('fingerprint_id_unique', 'unique(fingerprint_id)', "Fingerprint identifier must be unique! Please choose another one.")]
    
    def unlink(self):
        resources = self.mapped('resource_id')
        return True 
        #return resources.unlink()


    def button_generate_code(self):
        self.env.cr.execute("""
            select max(fingerprint_id::int)+1
            from hr_employee
            where fingerprint_id is not null and if_exclude is not True and active is True
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