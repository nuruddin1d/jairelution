# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class MrpRollLine(models.Model):
    _name = 'mrp.roll.line'
    _description = 'MRP Roll Line'

    production_id = fields.Many2one('mrp.production')
    jumbo_roll_length = fields.Float()
    jumbo_roll_qty = fields.Integer(default=1)
    weight_per_roll = fields.Float(compute='compute_weight_per_roll', store=True)
    roll_weight_with_trim = fields.Float(compute='compute_roll_weight_with_trim')
    roll_weight_without_trim = fields.Float(compute='compute_roll_weight_without_trim')

    # This method calculates weight with trim for one roll
    @api.depends('jumbo_roll_length', 'production_id.total_size', 'production_id.product_id')
    def compute_weight_per_roll(self):
        for line in self:
            line.weight_per_roll = 0.0
            weight_per_roll = 0
            product_id = line.production_id.product_id
            if product_id.micron > 0 and product_id.categ_id.density > 0 and line.production_id.total_size > 0 and line.jumbo_roll_length > 0:
                total_size = line.production_id.total_size
                weight_per_roll = (product_id.micron * total_size *
                                   product_id.categ_id.density * line.jumbo_roll_length) / 1000000
            line.weight_per_roll = weight_per_roll

    # This method calculates weight without trim
    @api.depends('jumbo_roll_length', 'jumbo_roll_qty', 'production_id.total_size', 'production_id.product_id')
    def compute_roll_weight_without_trim(self):
        for line in self:
            line.roll_weight_without_trim = 0.0
            roll_weight_without_trim = 0
            product_id = line.production_id.product_id
            if product_id.micron > 0 and product_id.categ_id.density > 0 and line.production_id.total_size > 0 and line.jumbo_roll_length > 0:
                total_size = line.production_id.total_size - line.production_id.trim_size
                roll_weight_without_trim = (product_id.micron * total_size *
                                            product_id.categ_id.density * line.jumbo_roll_length) / 1000000
            line.roll_weight_without_trim = roll_weight_without_trim * line.jumbo_roll_qty

    # This method calculates weight for their roll qty
    @api.depends('weight_per_roll', 'jumbo_roll_qty')
    def compute_roll_weight_with_trim(self):
        for line in self:
            line.roll_weight_with_trim = 0.0
            if line.jumbo_roll_qty > 0:
                line.roll_weight_with_trim = line.jumbo_roll_qty * line.weight_per_roll
