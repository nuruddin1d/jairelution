# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    planing_state = fields.Selection([
        ('unplanned', 'Not Plan'),
        ('planed', 'Planned'),
        ('partial_plan', 'Partial Plan'),
    ], string='Manufacturing Status', default='unplanned', tracking=True, compute='compute_mrp_state_from_line', store=True)

    @api.depends('order_line.line_planing_state')
    def compute_mrp_state_from_line(self):
        for rec in self:
            plan = len(rec.order_line.filtered(lambda r: r.line_planing_state == 'planed'))
            partial_plan = len(rec.order_line.filtered(lambda r: r.line_planing_state == 'partial_plan'))
            unplanned = len(rec.order_line.filtered(lambda r: r.line_planing_state == 'unplanned'))
            if partial_plan > 0 and plan == 0:
                rec.planing_state = 'partial_plan'
            elif plan > 0 and partial_plan == 0:
                rec.planing_state = 'planed'
            elif unplanned == len(rec.order_line):
                rec.planing_state = 'unplanned'
            else:
                rec.planing_state = 'unplanned'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_planing_state = fields.Selection([
        ('unplanned', 'Not Plan'),
        ('planed', 'Planned'),
        ('partial_plan', 'Partial Plan'),
    ], string='Manufacturing Status', default='unplanned', tracking=True, store=True)
    mrp_order_id = fields.Many2many('mrp.production', string='MRP Orders')




