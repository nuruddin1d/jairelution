# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class MrpExtruder(models.Model):
    _name = 'mrp.extruder'

    extruder_type = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')], string='Extruder Type', requierd=True)
    extruder_use = fields.Integer('Use of Extruder in %', requierd=True)
    extruder_total = fields.Float('Total', compute='compute_extruder_total', store=True)
    mrp_order_id = fields.Many2one('mrp.production')
    total_layer = fields.Float('Total Layer %')
    total_films = fields.Float('Total FILMS %', compute='compute_extruder_total')

    @api.depends('extruder_use', 'mrp_order_id.move_raw_ids.calculate_qty', 'mrp_order_id.move_raw_ids.row_unit')
    def compute_extruder_total(self):
        """compute extruder total and total_layer and total_films from manufacturing component to consume qty bases
        on extruder type"""
        for rec in self:
            rec.extruder_total = 0
            rec.total_layer = 0
            rec.total_films = 0
            total_layer = 0
            total_films_per = 0
            same_extruder = rec.mrp_order_id.move_raw_ids.filtered(lambda x: x.extruder_type == rec.extruder_type and x.row_unit != 'rpm' and x.material != 'is_adv')
            rec.extruder_total = sum([line.calculate_qty for line in same_extruder])
            for line in same_extruder:
                if rec.extruder_total > 0:
                    line.layer = (line.calculate_qty / rec.extruder_total) * 100
                    total_layer += line.layer
                    line.films = (line.layer * rec.extruder_use) / 100
                    line.product_uom_qty = (line.raw_material_production_id.product_qty * line.films) / 100
                    total_films_per += line.films
            rec.total_layer = total_layer
            rec.total_films = total_films_per
