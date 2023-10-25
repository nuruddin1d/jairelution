# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class MrpProductionLine(models.Model):
    _name = 'mrp.production.line'
    _description = 'MRP Production Line'

    production_id = fields.Many2one('mrp.production')
    product_id = fields.Many2one('product.product')
    multiply = fields.Integer(default=1)
    so_line_id = fields.Many2one('sale.order.line')
    so_line_qty = fields.Float()
    so_line_uom_id = fields.Many2one('uom.uom')
    so_line_clarity = fields.Char()
    so_line_density = fields.Float()
    so_line_sit = fields.Float()
    so_line_high_bond = fields.Char()
    so_line_size = fields.Float()
    so_line_weight = fields.Float(compute='compute_calculate_line_weight', store=True)
    is_completed = fields.Boolean('Is Completed')
    is_direct_production_line = fields.Boolean('Is Direct Production', related='production_id.is_direct_production')
    so_product_core = fields.Char('Core')
    so_sale_ct = fields.Char()
    so_sale_cof = fields.Char()
    so_roll_od = fields.Char()

    @api.onchange('so_line_id')
    def onchange_so_line(self):
        """This onchange method for set product and size from sale order line"""
        for line in self:
            if line.so_line_id:
                line.product_id = line.so_line_id.product_id.id
                line.so_line_size = line.so_line_id.size

    @api.onchange('product_id')
    def onchange_so_line(self):
        """This onchange method for set uom from product"""
        for line in self:
            if line.product_id and line.production_id.is_direct_production:
                line.so_line_uom_id = line.product_id.uom_id.id

    @api.depends('production_id.roll_line.jumbo_roll_length', 'production_id.roll_line.jumbo_roll_qty',
                 'production_id.total_size', 'so_line_size', 'production_id.product_id')
    def compute_calculate_line_weight(self):
        """This method calculates weight for individual size"""
        for line in self:
            line.so_line_weight = 0
            weight_per_size = 0
            product_id = line.production_id.product_id
            micron = product_id.micron
            total_size = (line.so_line_size * line.multiply)
            density = product_id.categ_id.density

            for roll in line.production_id.roll_line:
                if product_id and micron > 0 and total_size > 0 and density > 0 and roll.jumbo_roll_length > 0:
                    weight_per_size += ((micron * total_size * density * roll.jumbo_roll_length) / 1000000) * \
                                       roll.jumbo_roll_qty
            line.so_line_weight = weight_per_size

    def unlink(self):
        for rec in self:
            if rec.so_line_id:
                line_obj = rec.so_line_id
                mrp_id = rec.so_line_id.mrp_order_id.filtered(lambda r: r.id == rec.production_id.id)
                if mrp_id:
                    mrp_line_id = list(set(rec.so_line_id.mrp_order_id.ids) - set([mrp_id.id]))
                    rec.so_line_id.mrp_order_id = mrp_line_id if mrp_line_id else False
                    if rec.so_line_id.mrp_order_id:
                        continue
                    else:
                        line_obj.line_planing_state = 'unplanned'
        return super(MrpProductionLine, self).unlink()
