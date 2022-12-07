from odoo import _, api, fields, models

class IrActionsReport(models.Model):
    """Inherit from ir.actions.report to allow customizing the template
    file. The user cam chose a template from a list.
    The list is configurable in the configuration tab, see py3o_template.py
    """

    _inherit = "ir.actions.report"

    def _render_py3o(self, res_ids, data):
        if not res_ids:
            if self == self.env.ref('pathaka_py3o_report_fiscal.action_report_employee_pathakha'):
                res_ids = data['form'].get('self_ids')
        res = super()._render_py3o(res_ids, data)
        return res
