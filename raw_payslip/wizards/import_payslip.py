from odoo import models, fields, _
from odoo.exceptions import UserError

class ImportPayslip(models.TransientModel):
    _name = "import.payslip"

    imported = fields.Boolean(string="Imported", default=True)

    def import_payslip(self):
        if self._context.get('active_model') == 'raw.payslip':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('imported', '!=', True)]

        payslips = self.env['raw.payslip'].search(domain)
        if not payslips:
            raise UserError(_('There are no raw payslip to import to payslip.'))
        for payslip in payslips:
            if payslip.imported != True:
                rate = 0
                amount = 0
                # inverse_company_rate = 0
                company = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
                if payslip.employee_id:
                    employee = self.env['hr.employee'].sudo().search([('company_id', '=', company.id),('barcode', '=', payslip.employee_id)])
                    if not employee:
                        raise UserError(_("Employee ID %s doesn't exist.",payslip.employee_id))
                if not payslip.from_date:
                    raise UserError(_("Please fill from date."))
                if not payslip.to_date:
                    raise UserError(_("Please fill to date."))
                if payslip.currency:
                    currency = self.env['res.currency'].sudo().search([('name', '=', payslip.currency)])
                    if not currency:
                        raise UserError(_("Currency %s doesn't exist.",payslip.currency))
                contract = self.env['hr.contract'].sudo().search([('company_id', '=', company.id),('employee_id', '=', employee.id),('state', '=', 'open'),('currency_id', '=', currency.id)])
                if not contract:
                    raise UserError(_("There is no contract for employee ID %s.",payslip.employee_id))
                if contract and not contract.struct_id:
                    raise UserError(_("There is no structure in the contract of employee ID %s.",payslip.employee_id))
                else:
                    structure = contract.struct_id
                if payslip.subarea_description:
                    subarea = self.env['hr.subarea'].sudo().search([('name', '=', payslip.subarea_description)])
                    if not subarea:
                        raise UserError(_("Subarea %s doesn't exist.",payslip.subarea_description))
                if payslip.cost_centre:
                    cost_centre = self.env['account.analytic.account'].sudo().search([('company_id', '=', company.id),('name', '=', payslip.cost_centre)])
                    if not cost_centre:
                        raise UserError(_("Analytic account %s doesn't exist.",payslip.cost_centre))
                rule_mapping = self.env['salary.rule.mapping'].sudo().search([('company_id', '=', company.id)])
                if not rule_mapping:
                    raise UserError(_("Salary rule mapping for company %s doesn't exist.", company.name))
                else:
                    if payslip.rule1 != 0:
                        rule1_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 1')])
                        if not rule1_mapping:
                            raise UserError(_("Raw salary rule for rule1 doesn't exist."))
                        else:
                            rule1_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule1_mapping.id)])
                            if not rule1_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule1 doesn't exist."))
                    if payslip.rule2 != 0:
                        rule2_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 2')])
                        if not rule2_mapping:
                            raise UserError(_("Raw salary rule for rule2 doesn't exist."))
                        else:
                            rule2_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule2_mapping.id)])
                            if not rule2_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule2 doesn't exist."))
                    if payslip.rule3 != 0:
                        rule3_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 3')])
                        if not rule3_mapping:
                            raise UserError(_("Raw salary rule for rule3 doesn't exist."))
                        else:
                            rule3_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule3_mapping.id)])
                            if not rule3_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule3 doesn't exist."))
                    if payslip.rule4 != 0:
                        rule4_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 4')])
                        if not rule4_mapping:
                            raise UserError(_("Raw salary rule for rule4 doesn't exist."))
                        else:
                            rule4_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule4_mapping.id)])
                            if not rule4_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule4 doesn't exist."))
                    if payslip.rule5 != 0:
                        rule5_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 5')])
                        if not rule5_mapping:
                            raise UserError(_("Raw salary rule for rule5 doesn't exist."))
                        else:
                            rule5_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule5_mapping.id)])
                            if not rule5_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule5 doesn't exist."))
                    if payslip.rule6 != 0:
                        rule6_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 6')])
                        if not rule6_mapping:
                            raise UserError(_("Raw salary rule for rule6 doesn't exist."))
                        else:
                            rule6_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule6_mapping.id)])
                            if not rule6_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule6 doesn't exist."))
                    if payslip.rule7 != 0:
                        rule7_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 7')])
                        if not rule7_mapping:
                            raise UserError(_("Raw salary rule for rule7 doesn't exist."))
                        else:
                            rule7_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule7_mapping.id)])
                            if not rule7_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule7 doesn't exist."))
                    if payslip.rule8 != 0:
                        rule8_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 8')])
                        if not rule8_mapping:
                            raise UserError(_("Raw salary rule for rule8 doesn't exist."))
                        else:
                            rule8_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule8_mapping.id)])
                            if not rule8_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule8 doesn't exist."))
                    if payslip.rule9 != 0:
                        rule9_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 9')])
                        if not rule9_mapping:
                            raise UserError(_("Raw salary rule for rule9 doesn't exist."))
                        else:
                            rule9_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule9_mapping.id)])
                            if not rule9_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule9 doesn't exist."))
                    if payslip.rule10 != 0:
                        rule10_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 10')])
                        if not rule10_mapping:
                            raise UserError(_("Raw salary rule for rule10 doesn't exist."))
                        else:
                            rule10_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule10_mapping.id)])
                            if not rule10_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule10 doesn't exist."))
                    if payslip.rule11 != 0:
                        rule11_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 11')])
                        if not rule11_mapping:
                            raise UserError(_("Raw salary rule for rule11 doesn't exist."))
                        else:
                            rule11_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule11_mapping.id)])
                            if not rule11_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule11 doesn't exist."))
                    if payslip.rule12 != 0:
                        rule12_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 12')])
                        if not rule12_mapping:
                            raise UserError(_("Raw salary rule for rule12 doesn't exist."))
                        else:
                            rule12_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule12_mapping.id)])
                            if not rule12_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule12 doesn't exist."))
                    if payslip.rule13 != 0:
                        rule13_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 13')])
                        if not rule13_mapping:
                            raise UserError(_("Raw salary rule for rule13 doesn't exist."))
                        else:
                            rule13_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule13_mapping.id)])
                            if not rule13_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule13 doesn't exist."))
                    if payslip.rule14 != 0:
                        rule14_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 14')])
                        if not rule14_mapping:
                            raise UserError(_("Raw salary rule for rule14 doesn't exist."))
                        else:
                            rule14_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule14_mapping.id)])
                            if not rule14_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule14 doesn't exist."))
                    if payslip.rule15 != 0:
                        rule15_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 15')])
                        if not rule15_mapping:
                            raise UserError(_("Raw salary rule for rule15 doesn't exist."))
                        else:
                            rule15_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule15_mapping.id)])
                            if not rule15_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule15 doesn't exist."))
                    if payslip.rule16 != 0:
                        rule16_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 16')])
                        if not rule16_mapping:
                            raise UserError(_("Raw salary rule for rule16 doesn't exist."))
                        else:
                            rule16_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule16_mapping.id)])
                            if not rule16_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule16 doesn't exist."))
                    if payslip.rule17 != 0:
                        rule17_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 17')])
                        if not rule17_mapping:
                            raise UserError(_("Raw salary rule for rule17 doesn't exist."))
                        else:
                            rule17_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule17_mapping.id)])
                            if not rule17_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule17 doesn't exist."))
                    if payslip.rule18 != 0:
                        rule18_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 18')])
                        if not rule18_mapping:
                            raise UserError(_("Raw salary rule for rule18 doesn't exist."))
                        else:
                            rule18_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule18_mapping.id)])
                            if not rule18_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule18 doesn't exist."))
                    if payslip.rule19 != 0:
                        rule19_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 19')])
                        if not rule19_mapping:
                            raise UserError(_("Raw salary rule for rule19 doesn't exist."))
                        else:
                            rule19_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule19_mapping.id)])
                            if not rule19_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule19 doesn't exist."))
                    if payslip.rule20 != 0:
                        rule20_mapping = self.env['raw.salary.rule'].sudo().search([('name', '=', 'Rule 20')])
                        if not rule20_mapping:
                            raise UserError(_("Raw salary rule for rule20 doesn't exist."))
                        else:
                            rule20_mapping_line = self.env['salary.rule.mapping.line'].sudo().search([('mapping_id', '=', rule_mapping.id),('raw_salary_rule_id', '=', rule20_mapping.id)])
                            if not rule20_mapping_line:
                                raise UserError(_("Raw salary mapping line for rule20 doesn't exist."))
                payslip_vals = {
                    "name": "Salary Slip - " + employee.name + " - " + payslip.from_date.strftime("%B") + " " + payslip.from_date.strftime("%Y"),
                    "employee_id": employee.id,
                    "date_from": payslip.from_date,
                    "date_to": payslip.to_date,
                    "contract_id": contract.id,
                    "struct_id": structure.id,
                    "company_id": company.id,
                }
                emp_payslip = self.env['hr.payslip'].sudo().create(payslip_vals)
                if structure.input_line_type_ids:
                    for input_type in structure.input_line_type_ids:
                        # if company.currency_id.id != currency.id:
                        #     rate = self.env['res.currency.rate'].sudo().search([('company_id', '=', company.id),('currency_id', '=', currency.id),('name', '<=', fields.Datetime.now().date())],order='name desc',limit=1)
                        #     inverse_company_rate = rate.inverse_company_rate
                        mapping = self.env['salary.rule.mapping'].sudo().search([('company_id', '=', company.id)])
                        mapping_line = self.env['salary.rule.mapping.line'].sudo().search(
                            [('mapping_id', '=', mapping.id), ('input_type_id', '=', input_type.id)])
                        if mapping_line:
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 1':
                                amount = payslip.rule1
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 2':
                                amount = payslip.rule2
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 3':
                                amount = payslip.rule3
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 4':
                                amount = payslip.rule4
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 5':
                                amount = payslip.rule5
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 6':
                                amount = payslip.rule6
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 7':
                                amount = payslip.rule7
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 8':
                                amount = payslip.rule8
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 9':
                                amount = payslip.rule9
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 10':
                                amount = payslip.rule10
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 11':
                                amount = payslip.rule11
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 12':
                                amount = payslip.rule12
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 13':
                                amount = payslip.rule13
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 14':
                                amount = payslip.rule14
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 15':
                                amount = payslip.rule15
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 16':
                                amount = payslip.rule16
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 17':
                                amount = payslip.rule17
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 18':
                                amount = payslip.rule18
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 19':
                                amount = payslip.rule19
                            if mapping_line.raw_salary_rule_id and mapping_line.raw_salary_rule_id.name == 'Rule 20':
                                amount = payslip.rule20
                        input_type_line = self.env['hr.payslip.input'].sudo().search(
                            [('payslip_id', '=', emp_payslip.id), ('input_type_id', '=', input_type.id)])
                        if not input_type_line:
                            input_type_line_vals = {
                                "input_type_id": input_type.id,
                                "amount": amount,
                                "payslip_id": emp_payslip.id
                            }
                            payslip_input = self.env['hr.payslip.input'].sudo().create(input_type_line_vals)
                            amount = 0
                        else:
                            input_type_line.write({"amount": amount})
                            amount = 0
                payslip.write({"imported": True})
        return {'type': 'ir.actions.act_window_close'}
