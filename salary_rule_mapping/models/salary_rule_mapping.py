from odoo import api, fields, models, _

class SalaryRuleMapping(models.Model):
    _name = 'salary.rule.mapping'

    company_id = fields.Many2one('res.company', 'Company')
    line_ids = fields.One2many('salary.rule.mapping.line', 'mapping_id', string='Mapping Lines')

class SalaryRuleMappingLine(models.Model):
    _name = 'salary.rule.mapping.line'

    mapping_id = fields.Many2one('salary.rule.mapping', string='Salary Rule Mapping')
    raw_salary_rule_id = fields.Many2one('raw.salary.rule', string='Raw Salary Rule', required=True)
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule', required=False)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Input Type', required=True)
