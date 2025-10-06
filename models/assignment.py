from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class ProductAssignment(models.Model):
    _name = 'product.assignment'
    _description = 'Product Assignment'
    # _order = 'deadline asc'

    name = fields.Char(string=_('Assignment Name'), required=True, copy=False, readonly=True, default='New')
    product_id = fields.Many2one('product.product', string=_('Product'), required=True)
    contact_id = fields.Many2one('res.partner', string=_('Contact'), required=True)
    quantity = fields.Float(string=_('Quantity'), required=True)
    assignment_date = fields.Date(string=_('Assignment Date'), readonly=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string=_('Status'), default='draft', required=True, copy=False)
    stock_move_id = fields.Many2one('stock.move', string=_('Stock Move'), readonly=True)
    notes = fields.Text(string=_('Notes'))
    serial_number = fields.Char(string=_('Serial Number'))
    user_id = fields.Many2one('res.users', string=_('Assigned By'), default=lambda self: self.env.user, readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.product.assignment') or _('New')
        record = super(ProductAssignment, self).create(vals)
        return record
    
    def write(self, vals):
        for record in self:
            if record.state == 'done':
                raise UserError(_('No se puede modificar una asignación que ya está marcada como "Hecha".'))
        return super(ProductAssignment, self).write(vals)

    def action_assign(self):
        for record in self:
            if record.state == 'draft':
                record.write({
                    'state': 'assigned',
                    'assignment_date': fields.Date.today()
                })
        return True

    def action_done(self):
        self.write({'state': 'done'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        return True