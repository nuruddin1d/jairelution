# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SelectOrderLine(models.TransientModel):
    _name = 'select.order.line'
    _description = 'Select Order Line'

    order_line_ids = fields.Many2many('sale.order.line', string='Order Lines')
    product_id = fields.Many2one('product.product')
    categ_id = fields.Many2one(related='product_id.categ_id')
    micron = fields.Integer(related='product_id.micron')

    def default_get(self, fields):
        res = super(SelectOrderLine, self).default_get(fields)
        production_id = self.env['mrp.production'].browse(self._context.get('active_id', False))
        res['product_id'] = production_id.product_id.id
        return res

    def select_order_lines(self):
        production_id = self.env['mrp.production'].browse(self._context.get('active_id', False))
        for line in self.order_line_ids:
            self.env['mrp.production.line'].create({
                'so_line_id': line.id,
                'so_line_size': line.size,
                'production_id': production_id.id,
                'so_line_uom_id': line.product_uom.id,
                'so_line_qty': line.product_uom_qty,
                'so_line_clarity': line.clarity,
                'so_line_density': line.optical_density,
                'so_line_sit': line.line_sit,
                'so_line_high_bond': line.high_bond,
                'so_product_core': line.product_core,
                'so_sale_ct': line.sale_ct,
                'so_sale_cof': line.sale_cof,
                'so_roll_od': line.roll_od,
            })

    @api.onchange('order_line_ids')
    def order_line_domain(self):
        lines = []
        for rec in self:
            if rec.product_id:
                line_obj = self.env['sale.order.line'].search([('line_planing_state', 'in', ['unplanned', 'partial_plan']), ('state', 'in', ['sale', 'done'])])
                for line in line_obj:
                    if rec.product_id.micron == line.product_id.micron and rec.product_id.categ_id.category_code == line.product_id.categ_id.category_code:
                        lines.append(line.id)
        domain = {"order_line_ids": [("id", "in", lines)]}
        return {"domain": domain}
