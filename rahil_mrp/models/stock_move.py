# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import Warning
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet


class StockMove(models.Model):
    _inherit = 'stock.move'

    material = fields.Selection([('is_rm', 'Raw Material'), ('is_adv', 'Additives')], default='is_rm')
    extruder_type = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')])
    layer = fields.Float('Layer %')
    films = fields.Float('FILMS %')
    row_unit = fields.Selection([('kg', 'kgs'), ('rpm', 'RPM')], default='kg', string='Unit')
    calculate_qty = fields.Float('Calc Qty')
    move_component_lot_ids = fields.Many2many('stock.production.lot', string='Lots')

    @api.onchange('row_unit')
    def changes_layer_and_films(self):
        """This onchange for set layer and films zero when unit is RPM"""
        for rec in self:
            layer = 0
            films = 0
            if rec.row_unit == 'rpm':
                rec.layer = layer
                rec.films = films

    @api.onchange('material')
    def onchange_raw_material(self):
        if self.raw_material_production_id.work_order_type == 'cast':
            if self.material:
                self.product_id = False
                return {'domain': {'product_id': [('is_raw_material', '=', True)]}}
            else:
                return {'domain': {'product_id': []}}

    # @api.onchange('stock_lot_ids')
    # def onchange_set_lot_to_move_line(self):
    #     """This method for create stock move line from lot no. selected no lot no field"""
    #     for rec in self:
    #         for lot_id in rec.stock_lot_ids:
    #             exiting_id = rec.move_line_ids.filtered(lambda x: x.lot_id == lot_id)
    #             quant = lot_id.quant_ids.filtered(lambda q: q.location_id.usage == 'internal')
    #             if sum(quant.mapped('available_quantity')) <= 0:
    #                 raise ValidationError(
    #                     _('selected lot has negative available quantity or its already reserved somewhere !'))
    #             if exiting_id:
    #                 continue
    #             else:
    #                 if lot_id:
    #                     vals = {
    #                         'lot_id':  lot_id._origin.id,
    #                         'product_id': rec.product_id.id,
    #                         'move_id': rec.id,
    #                         'product_uom_qty': lot_id.product_qty,
    #                         'qty_done': lot_id.product_qty,
    #                         'product_uom_id': lot_id.product_uom_id.id,
    #                     }
    #                     rec.move_line_ids.create(vals)
    #         if not rec.stock_lot_ids:
    #             for move_line in rec.move_line_ids:
    #                 move_line.qty_done = 0
    #                 move_line.product_uom_qty = 0
    #                 move_line.unlink()

    # @api.onchange('product_id')
    # def check_product_forcast_qty(self):
    #     """This method check forcast quantity in product if not then raise validation"""
    #     for rec in self:
    #         if rec.product_id.virtual_available < 0:
    #             raise ValidationError(_('Your product has negative forcast quantity please update quantity'))
