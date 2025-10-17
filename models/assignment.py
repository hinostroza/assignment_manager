from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductAssignment(models.Model):
    _name = 'product.assignment'
    _description = 'Product Assignment'
    
    name = fields.Char(string=_('Code'), required=True, copy=False, readonly=True, default='New')
    contact_id = fields.Many2one('res.partner', string=_('Contact'), required=True)
    assignment_date = fields.Date(string=_('Assignment Date'), readonly=True, copy=False)
    state = fields.Selection([
        ('draft', _('Draft')),
        ('assigned', _('Assigned')),
        ('done', _('Done')),
        ('cancel', _('Cancelled')),
    ], string=_('Status'), default='draft', required=True, copy=False, tracking=True)
    
    # Campo One2many para las líneas de asignación
    assignment_line_ids = fields.One2many('product.assignment.line', 'assignment_id', string=_('Assignment Lines'))
    
    # Campo Many2many para ver todos los movimientos de stock generados
    stock_move_ids = fields.Many2many('stock.move', string=_('Stock Moves'), readonly=True, copy=False)
    
    notes = fields.Text(string=_('Notes'))
    user_id = fields.Many2one('res.users', string=_('Assigned By'), default=lambda self: self.env.user, readonly=True)

    # Campo para múltiples adjuntos
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', copy=False)

    @api.constrains('assignment_line_ids')
    def _check_lines(self):
        for record in self:
            if not record.assignment_line_ids:
                raise ValidationError(_("You must add at least one product line."))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.product.assignment') or _('New')
        record = super(ProductAssignment, self).create(vals)
        return record

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        """
        Extend search to include the contact's name.
        """
        args = args or []
        domain = args
        if name:
            # Search in assignment code OR contact name
            domain = ['|', ('name', operator, name), ('contact_id.name', operator, name)]
        return self._search(domain + args, limit=limit, order=order)
        
    def _get_customer_location(self, partner):
        """Helper to find the customer location."""
        # En Odoo 18, la forma correcta de obtener la ubicación del cliente es
        # a través del campo de propiedad en el partner.
        # Este campo es 'property_stock_customer'.
        return partner.property_stock_customer
    
    def action_assign(self):
        for record in self:
            if record.state == 'draft':
                record.write({
                    'state': 'assigned',
                    'assignment_date': fields.Date.today()
                })
        return True

    def action_done(self):
        moves_to_process = self.env['stock.move']
        for record in self:
            if record.state != 'assigned':
                raise UserError(_('Only assignments in the "Assigned" state can be marked as "Done".'))
            
            if not record.assignment_line_ids:
                raise UserError(_('You cannot mark as done an assignment with no product lines.'))

            # Obtener ubicaciones (una sola vez por registro)
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', record.env.company.id)], limit=1)
            if not warehouse:
                raise UserError(_('No warehouse found for the company %s.') % (record.env.company.name,))
            
            source_location = warehouse.lot_stock_id
            dest_location = self._get_customer_location(record.contact_id)
            if not dest_location:
                raise UserError(_('The customer location could not be found. Please configure it.'))
            
            # Iterar sobre cada línea de producto
            for line in record.assignment_line_ids:
                # 1. Validar número de serie si es requerido en la línea
                if line.product_tracking != 'none' and not line.serial_number:
                    raise UserError(_('Product "%s" requires a Lot/Serial number.') % line.product_id.name)

                # 2. Crear el movimiento de stock para la línea
                move_vals = {
                    'name': _('Assignment: %s') % record.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': source_location.id,
                    'location_dest_id': dest_location.id,
                    'origin': record.name,
                    'company_id': record.env.company.id,
                    'state': 'confirmed',
                }
                move = self.env['stock.move'].create(move_vals)

                # 3. Validar disponibilidad y asignar lote/serie
                available_qty = self.env['stock.quant']._get_available_quantity(line.product_id, source_location)
                if available_qty < line.quantity:
                    raise UserError(_('Not enough stock for product "%s". Available: %s, Requested: %s.') % (line.product_id.name, available_qty, line.quantity))

                lot = False
                if line.product_tracking != 'none':
                    lot = self.env['stock.lot'].search([
                        ('name', '=', line.serial_number),
                        ('product_id', '=', line.product_id.id),
                        ('company_id', '=', record.env.company.id),
                    ], limit=1)
                    if not lot:
                        raise UserError(_('Serial Number "%s" not found for product "%s".') % (line.serial_number, line.product_id.name))

                move.write({
                    'quantity': line.quantity,
                    'picked': True,
                })

                if lot:
                    move.move_line_ids.lot_id = lot.id
                
                moves_to_process |= move

            # 4. Validar todos los movimientos de stock creados
            if moves_to_process:
                moves_to_process._action_done()

            # 5. Actualizar el estado de la asignación y guardar los movimientos.
            record.write({
                'state': 'done',
                'stock_move_ids': [(6, 0, moves_to_process.ids)]
            })

    def action_cancel(self):
        # Si hay un movimiento de stock asociado, cancelarlo también.
        moves_to_cancel = self.mapped('stock_move_ids').filtered(lambda m: m.state not in ('done', 'cancel'))
        if moves_to_cancel:
            moves_to_cancel._action_cancel()
        self.write({'state': 'cancel'})
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_("You cannot delete an assignment that is in the 'Done' state."))
        return super(ProductAssignment, self).unlink()


class ProductAssignmentLine(models.Model):
    _name = 'product.assignment.line'
    _description = 'Product Assignment Line'

    assignment_id = fields.Many2one('product.assignment', string=_('Assignment Reference'), required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string=_('Product'), required=True)
    quantity = fields.Float(string=_('Quantity'), required=True, default=1.0)
    serial_number = fields.Char(string=_('Lot/Serial Number (Inventory)'))
    warranty_sn = fields.Char(string=_('SN (Warranty/Informational)'))
    purchase_date = fields.Date(string=_('Purchase Date'))
    
    handle_separator = fields.Char(string=" ", readonly=True)
    # Campos relacionados para facilitar la lógica en la vista
    product_tracking = fields.Selection(related='product_id.tracking', readonly=True)
    state = fields.Selection(related='assignment_id.state', string=_('Status'), readonly=True)

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('The quantity must be greater than 0 for product %s.') % line.product_id.display_name)
            if line.product_id.tracking == 'serial' and line.quantity != 1:
                raise ValidationError(_('For product %s (tracked by unique serial number), the quantity must be 1.') % line.product_id.display_name)

    @api.constrains('serial_number', 'product_id')
    def _check_serial_number(self):
        for line in self:
            if line.product_tracking == 'serial' and not line.serial_number:
                raise ValidationError(_("A serial number is required for product %s.") % line.product_id.display_name)