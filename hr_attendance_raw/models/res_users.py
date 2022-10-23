from odoo import fields, models, api, _


class ResUser(models.Model):
    _inherit = 'res.users'

    @api.constrains('groups_id')
    def _check_one_user_type(self):
        """We check that no users are both portal and users (same with public).
           This could typically happen because of implied groups.
        """
        user_types_category = self.env.ref('base.module_category_user_type', raise_if_not_found=False)
        user_types_groups = self.env['res.groups'].search(
            [('category_id', '=', user_types_category.id)]) if user_types_category else False
#         if user_types_groups:  # needed at install
#             if self._has_multiple_groups(user_types_groups.ids):
#                 raise ValidationError(_('The user cannot have more than one user types.'))
#                 #raise ValidationError(_("The user cannot have more than one user types (%s) (%s) (%s).") % (user_types_groups, user_types_groups.ids,user_types_category.id))
