from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    assignment_count = fields.Integer(compute='_compute_assignment_count', string='Assignment Count')

    def _compute_assignment_count(self):
        for partner in self:
            partner.assignment_count = self.env['product.assignment'].search_count([('contact_id', '=', partner.id)])

    def action_view_assignments(self):
        return {
            'name': _('Product Assignments'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.assignment',
            'view_mode': 'list,form',
            'domain': [('contact_id', '=', self.id)],
        }