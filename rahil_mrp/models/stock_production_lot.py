# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    roll_count = fields.Integer('Roll No.', default=1)
    micron = fields.Integer(string='Micron')
    length = fields.Float('Length')
    size = fields.Integer(string='Size')
    type = fields.Many2one('product.category', string='Type')
    gross_weight = fields.Float('Gross Weight')
    no_of_joint = fields.Integer('No. of Joint')
    work_type = fields.Selection([('cast', 'Cast'), ('slit', 'Slit'), ('mate', 'Mate'), ('rewind', 'Rewind')],
                                 default='cast')
    product_core = fields.Char(string='Core', store=True)
    sale_ct = fields.Char(string='CT', store=True)
    sale_cof = fields.Char(string='COF', store=True)
    roll_od = fields.Char(string='Roll OD', store=True)
    order_ids = fields.Many2many('sale.order')
    order_id = fields.Many2one('sale.order')