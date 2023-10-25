# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import OrderedSet, format_date, groupby as tools_groupby

SIZE_BACK_ORDER_NUMERING = 3


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    micron = fields.Integer(related='product_id.micron')
    line_no = fields.Selection([('line1', 'Line 1'), ('line2', 'Line 2')])
    sale_order_line = fields.One2many('sale.order.line', 'mrp_order_id', string="Orders")
    mrp_product_ids = fields.One2many('product.product', 'mrp_id', compute='compute_pro_id_for_domain',
                                      string="Products", store=True)
    partner_ids = fields.Many2many('res.partner')
    order_ids = fields.Many2many('sale.order')
    trim_size = fields.Float(default=30.0)
    total_size = fields.Float(compute='compute_total_size', store=True)
    jumbo_roll_size = fields.Float()
    total_jumbo_roll = fields.Integer()
    total_jumbo_roll_length = fields.Float()
    roll_weight_without_trim = fields.Float(compute='compute_roll_weight_without_trim', store=True)
    roll_weight_with_trim = fields.Float(compute='compute_roll_weight_with_trim', store=True)
    production_line = fields.One2many('mrp.production.line', 'production_id')
    roll_line = fields.One2many('mrp.roll.line', 'production_id')
    product_qty = fields.Float(compute='compute_total_weight', store=True)
    extruder_line_ids = fields.One2many('mrp.extruder', 'mrp_order_id', string='Extruders')
    is_direct_production = fields.Boolean('Is Direct Production')
    is_slitter_view = fields.Boolean('Is Slitter view')
    work_count = fields.Integer('Work Line Count', compute='_compute_work_count')
    sale_order_counts = fields.Integer('Sale order Count', compute='_compute_work_count')
    slitting_reason = fields.Text(string="Slitting Reason")
    slitter_line = fields.Selection([('line1', 'Line 1'), ('line2', 'Line 2'), ('line3', 'Line 3')])
    is_metalized = fields.Boolean('Is Metalised', default=False)
    is_rewinding = fields.Boolean('Is Metalised', default=False)
    work_order_type = fields.Selection([('cast', 'Cast'), ('slit', 'Slit'), ('mate', 'Mate'), ('rewind', 'Rewind')], default='cast',
                                       string='Work Order Type')
    parent_mo_ids = fields.Many2many('mrp.production', 'rel_parent_mrp', 'child_id', 'parent_id', 'Parent MRP Orders')
    component_lot_ids = fields.Many2many('stock.production.lot', string='Lots')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('hold', 'Hold')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")

    def default_get(self, fields):
        """This method use for creating the default extruder line when mo is created."""
        res = super(MrpProduction, self).default_get(fields)
        extruder = []
        extruder_line1 = {
            'extruder_type': 'a',
        }
        extruder.append((0, 0, extruder_line1))
        extruder_line2 = {
            'extruder_type': 'b',
        }
        extruder.append((0, 0, extruder_line2))
        extruder_line3 = {
            'extruder_type': 'c',
        }
        extruder.append((0, 0, extruder_line3))
        res['extruder_line_ids'] = extruder
        return res

    # def _post_inventory(self, cancel_backorder=False):
    #     """Override this method for producing the mass lot numbers from one MO.
    #         Also, it sets the last lot number from work entry as Manufacture order lot."""
    #     moves_to_do, moves_not_to_do = set(), set()
    #     for move in self.move_raw_ids:
    #         if move.state == 'done':
    #             moves_not_to_do.add(move.id)
    #         elif move.state != 'cancel':
    #             moves_to_do.add(move.id)
    #             if move.product_qty == 0.0 and move.quantity_done > 0:
    #                 move.product_uom_qty = move.quantity_done
    #     self.env['stock.move'].browse(moves_to_do)._action_done(cancel_backorder=cancel_backorder)
    #     moves_to_do = self.move_raw_ids.filtered(lambda x: x.state == 'done') - self.env['stock.move'].browse(
    #         moves_not_to_do)
    #     # Create a dict to avoid calling filtered inside for loops.
    #     moves_to_do_by_order = defaultdict(lambda: self.env['stock.move'], [
    #         (key, self.env['stock.move'].concat(*values))
    #         for key, values in tools_groupby(moves_to_do, key=lambda m: m.raw_material_production_id.id)
    #     ])
    #     for order in self:
    #         finish_moves = order.move_finished_ids.filtered(
    #             lambda m: m.product_id == order.product_id and m.state not in ('done', 'cancel'))
    #         # the finish move can already be completed by the workorder.
    #         if finish_moves and not finish_moves.quantity_done:
    #             work_line_ids = self.env['mrp.work.line'].search([('mrp_order', '=', order.id), ('qc_status', '=', 'confirm')])
    #             for entry in work_line_ids:
    #                 finish_moves._set_quantity_done(float_round(entry.net_weight,
    #                                                             precision_rounding=order.product_uom_id.rounding,
    #                                                             rounding_method='HALF-UP'))
    #                 for move_line in finish_moves.move_line_ids:
    #                     if not move_line.lot_id:
    #                         move_line.lot_id = entry.lot_id.id
    #             if work_line_ids:
    #                 order.lot_producing_id = work_line_ids[-1].lot_id
    #             # finish_moves._set_quantity_done(float_round(order.qty_producing - order.qty_produced, precision_rounding=order.product_uom_id.rounding, rounding_method='HALF-UP'))
    #             # finish_moves.move_line_ids.lot_id = order.lot_producing_id
    #         order._cal_price(moves_to_do_by_order[order.id])
    #     moves_to_finish = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #     moves_to_finish = moves_to_finish._action_done(cancel_backorder=cancel_backorder)
    #     self.action_assign()
    #     for order in self:
    #         consume_move_lines = moves_to_do_by_order[order.id].mapped('move_line_ids')
    #         order.move_finished_ids.move_line_ids.consume_line_ids = [(6, 0, consume_move_lines.ids)]
    #     return True

    def button_mark_done(self):
        work_line_ids = self.env['mrp.work.line'].search([('mrp_order', '=', self.id), ('qc_status', '=', 'confirm')])
        pen_work_line_ids = self.env['mrp.work.line'].search([('mrp_order', '=', self.id), ('qc_status', '=', 'draft')])
        if pen_work_line_ids:
            raise ValidationError(_('One of your production entry pending for quality check'))
        if work_line_ids:
            self.lot_producing_id = work_line_ids[-1].lot_id
        return super(MrpProduction, self).button_mark_done()

    def _post_inventory(self, cancel_backorder=False):
        """Override this method for producing the mass lot numbers from one MO.
            Also, it sets the last lot number from work entry as Manufacture order lot."""
        moves_to_do, moves_not_to_do = set(), set()
        for move in self.move_raw_ids:
            if move.state == 'done':
                moves_not_to_do.add(move.id)
            elif move.state != 'cancel':
                moves_to_do.add(move.id)
                if move.product_qty == 0.0 and move.quantity_done > 0:
                    move.product_uom_qty = move.quantity_done
        self.env['stock.move'].browse(moves_to_do)._action_done(cancel_backorder=cancel_backorder)
        moves_to_do = self.move_raw_ids.filtered(lambda x: x.state == 'done') - self.env['stock.move'].browse(
            moves_not_to_do)
        # Create a dict to avoid calling filtered inside for loops.
        moves_to_do_by_order = defaultdict(lambda: self.env['stock.move'], [
            (key, self.env['stock.move'].concat(*values))
            for key, values in tools_groupby(moves_to_do, key=lambda m: m.raw_material_production_id.id)
        ])
        for order in self:
            finish_moves = order.move_finished_ids.filtered(
                lambda m: m.product_id == order.product_id and m.state not in ('done', 'cancel'))
            # the finish move can already be completed by the workorder.
            if finish_moves and not finish_moves.quantity_done:
                work_line_ids = self.env['mrp.work.line'].search(
                    [('mrp_order', '=', order.id), ('qc_status', '=', 'confirm')])
                # for entry in work_line_ids:
                #     finish_moves._set_quantity_done(float_round(entry.net_weight,
                #                                                 precision_rounding=order.product_uom_id.rounding,
                #                                                 rounding_method='HALF-UP'))
                #     for move_line in finish_moves.move_line_ids:
                #         if not move_line.lot_id:
                #             move_line.lot_id = entry.lot_id.id
                if work_line_ids:
                    order.lot_producing_id = work_line_ids[-1].lot_id
                # finish_moves._set_quantity_done(float_round(order.qty_producing - order.qty_produced, precision_rounding=order.product_uom_id.rounding, rounding_method='HALF-UP'))
                # finish_moves.move_line_ids.lot_id = order.lot_producing_id
            order._cal_price(moves_to_do_by_order[order.id])
        moves_to_finish = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_to_finish = moves_to_finish._action_done(cancel_backorder=cancel_backorder)
        self.action_assign()
        for order in self:
            consume_move_lines = moves_to_do_by_order[order.id].mapped('move_line_ids')
            order.move_finished_ids.move_line_ids.consume_line_ids = [(6, 0, consume_move_lines.ids)]
        return True

    @api.onchange('product_id', 'line_no')
    def onchange_product_id(self):
        """This method raise the warning when user trying to produce more than 3200 KG in line2."""
        for mo in self:
            if mo.product_id and mo.line_no:
                if mo.line_no == 'line2' and mo.product_qty > 3200:
                    return {
                        'warning': {
                            'title': _('Warning'),
                            'message': _(
                                'You are trying to produce more than 3200 KG in Line 2.')
                        }
                    }

    @api.depends('trim_size', 'production_line.so_line_size', 'production_line.multiply')
    def compute_total_size(self):
        """This method calculates the total size"""
        self.total_size = 0
        for record in self:
            size = 0
            for line in record.production_line:
                size += line.so_line_size * line.multiply
            if record.trim_size > 0 and size > 0:
                record.total_size = record.trim_size + size

    @api.depends('roll_line.roll_weight_with_trim')
    def compute_roll_weight_with_trim(self):
        """This method calculates the total weight of with trim roll"""
        self.roll_weight_with_trim = 0
        for mo in self:
            roll_weight_with_trim = 0
            for line in mo.roll_line:
                roll_weight_with_trim += line.roll_weight_with_trim
            mo.roll_weight_with_trim = roll_weight_with_trim

    @api.depends('roll_line.roll_weight_without_trim')
    def compute_roll_weight_without_trim(self):
        """This method calculates the total weight of without trim roll"""
        self.roll_weight_without_trim = 0
        for mo in self:
            roll_weight_without_trim = 0
            for line in mo.roll_line:
                roll_weight_without_trim += line.roll_weight_without_trim
            mo.roll_weight_without_trim = roll_weight_without_trim

    def manage_mrp_status_in_sales_line(self):
        """This method manage the status of the sale order line"""
        for rec in self:
            for line in rec.production_line:
                if line.so_line_id:
                    if line.so_line_weight >= line.so_line_qty:
                        line.so_line_id.mrp_order_id = [(4, rec.id)]
                        line.so_line_id.line_planing_state = 'planed'
                    elif line.so_line_weight < line.so_line_qty:
                        line.so_line_id.mrp_order_id = [(4, rec.id)]
                        line.so_line_id.line_planing_state = 'partial_plan'
                    else:
                        line.so_line_id.line_planing_state = 'unplanned'
                if line.is_completed:
                    line.so_line_id.mrp_order_id = [(4, rec.id)]
                    line.so_line_id.line_planing_state = 'planed'

    @api.model
    def create(self, vals_list):
        rec = super(MrpProduction, self).create(vals_list)
        if rec:
            rec.manage_mrp_status_in_sales_line()
        return rec

    def write(self, vals):
        rec = super(MrpProduction, self).write(vals)
        if rec:
            self.manage_mrp_status_in_sales_line()
            self.update_mrp_gty_in_sale()
        return rec

    @api.depends('production_line.so_line_weight')
    def compute_total_weight(self):
        """This method calculate Product qty from sum of production line weight"""
        qty = 0
        for rec in self:
            if rec.work_order_type == 'cast':
                rec.product_qty = 1
                for pro_line in rec.production_line:
                    if pro_line.so_line_weight > 0:
                        qty += pro_line.so_line_weight
                        rec.product_qty = qty
            else:
                rec.product_qty = 1
                for line in rec.move_raw_ids:
                    if line.product_uom_qty > 0:
                        qty += line.product_uom_qty
                        rec.product_qty = qty

    def update_mrp_gty_in_sale(self):
        """This method calculate mrp qty in sale order from production line weight."""
        qty = 0
        for rec in self:
            for pro_line in rec.production_line:
                if pro_line.so_line_weight > 0:
                    qty = pro_line.so_line_weight
                pro_line.so_line_id.mrp_qty = qty

    @api.depends('order_ids')
    def compute_pro_id_for_domain(self):
        """compute product domain from order line's product"""
        pro_ids = []
        micron = []
        for rec in self:
            rec.mrp_product_ids = False
            if rec.order_ids:
                for so in rec.order_ids:
                    for line in so.order_line:
                        if line.line_planing_state not in ['planed']:
                            pro_ids.append(line.product_id.id)
                            micron.append(line.micron)
            if pro_ids and micron:
                product_ids = self.env['product.product'].search(
                    ['|', ("id", "in", pro_ids), '&', ('micron', 'in', micron), ('size', '=', 0)])
            else:
                product_ids = self.env['product.product'].search([])
            rec.mrp_product_ids = [(6, 0, product_ids.ids)]

    def action_view_work_entry(self):
        self.ensure_one()
        for rec in self:
            ids = self.env['mrp.work.line'].search([('mrp_order', '=', rec.id)]).ids
            action = {
                'res_model': 'mrp.work.line',
                'type': 'ir.actions.act_window',
                'name': _('Work Lines'),
                'domain': [('id', 'in', ids)],
                'view_mode': 'tree',
            }
            return action

    def action_view_sale_order(self):
        self.ensure_one()
        for rec in self.order_ids:
            action = {
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
            }
            if len(self.order_ids) == 1:
                action.update({
                    'view_mode': 'form',
                    'res_id': rec[0].id,
                })
            else:
                action.update({
                    'name': 'Sale Orders',
                    'domain': [('id', 'in', self.order_ids.ids)],
                    'view_mode': 'tree,form',
                })
            return action

    def quick_create_work(self):
        self.ensure_one()
        for rec in self:
            ids = self.env['mrp.work'].search([('mrp_order', '=', rec.id)]).ids
            view_id = self.env.ref('rahil_mrp.quick_create_rahil_mrp_work_view_form').id
            if ids:
                action = {
                    'res_model': 'mrp.work',
                    'type': 'ir.actions.act_window',
                    'name': _('Work Lines'),
                    'view_mode': 'form',
                    'target': 'new',
                    'views': [[view_id, 'form']],
                    'view_id': view_id,
                    'res_id': ids[0],
                }
                return action
            else:
                action2 = {
                    'res_model': 'mrp.work',
                    'type': 'ir.actions.act_window',
                    'name': _('Work order'),
                    'view_mode': 'from',
                    'target': 'new',
                    'context': {'default_mrp_order': rec.id, 'default_work_type': rec.work_order_type},
                    'views': [[view_id, 'form']],
                }
                return action2

    def _compute_work_count(self):
        self.work_count = 0
        self.sale_order_counts = 0
        for rec in self:
            rec.work_count = len(self.env['mrp.work.line'].search([('mrp_order', '=', rec.id)]))
            rec.sale_order_counts = len(rec.order_ids.ids)

    @api.onchange('qty_producing')
    def change_to_consumption(self):
        for rec in self:
            for mrp_line in rec.move_raw_ids:
                if rec.product_qty and mrp_line.films:
                    mrp_line.quantity_done = rec.qty_producing * mrp_line.films

    @api.onchange('component_lot_ids')
    def lot_create_component(self):
        if self.work_order_type in ['rewind', 'mate', 'slit'] and self.component_lot_ids and self.state == 'draft':
            for comp_lot in self.component_lot_ids:
                same_product_lot = self.component_lot_ids.filtered(
                    lambda x: x.product_id != comp_lot.product_id) - comp_lot
                if same_product_lot:
                    raise ValidationError(_("You can't select different product lot!"))
                if self.move_raw_ids:
                    for move in self.move_raw_ids:
                        if comp_lot._origin not in move.move_component_lot_ids._origin:
                            move['product_uom_qty'] += comp_lot.product_qty
                            move['move_component_lot_ids'] = [(4, comp_lot._origin.id)]
                        if len(move.move_component_lot_ids._origin) > len(self.component_lot_ids._origin):
                            deleted_ids = move.move_component_lot_ids._origin - self.component_lot_ids._origin
                            for delete_id in deleted_ids:
                                move['product_uom_qty'] -= delete_id.product_qty
                                move['move_component_lot_ids'] = [(3, delete_id.id)]
                if comp_lot.product_id and not self.move_raw_ids:
                    data = self._get_move_raw_values(
                        comp_lot.product_id,
                        comp_lot.product_qty,
                        comp_lot.product_uom_id,
                        self.picking_type_id.id,
                    )
                    location = self.env['stock.location'].search([('usage', '=', 'production')])
                    data.update({
                        'move_component_lot_ids': [(4, comp_lot.id)],
                        'location_dest_id': location.id,
                        })
                    self.move_raw_ids = [(0, 0, data)]
        if not self.component_lot_ids and self.work_order_type in ['rewind', 'mate', 'slit'] and self.state == 'draft':
            self.move_raw_ids = [(5,)]

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        if self.work_order_type in ['rewind', 'mate', 'slit'] and self.component_lot_ids:
            for move in self.move_raw_ids:
                mrp_ids = []
                sale_order_ids = []
                if move.move_line_ids:
                    for move_line in move.move_line_ids:
                        move['move_line_ids'] = [(3, move_line.id)]
                for lot in self.component_lot_ids:
                    vals = move._prepare_move_line_vals(quantity=lot.product_qty)
                    vals.update({'lot_id': lot.id, 'lot_name': lot.name, 'qty_done': lot.product_qty})
                    move_line = self.env['stock.move.line'].create(vals)
                    move_line.write({'qty_done': lot.product_qty})
                    for order in lot.order_ids:
                        if order in sale_order_ids:
                            continue
                        else:
                            sale_order_ids.append(order.id)
                work_line_ids = self.env['mrp.work.line'].search([('lot_id.name', '=', lot.name)])
                for work in work_line_ids:
                    mrp_ids.append(work.mrp_order.id)
                self.parent_mo_ids = [(6, 0, mrp_ids)]
                self.order_ids = [(6, 0, sale_order_ids)]
            return res

    def action_hold(self):
        self.state = 'hold'

    def action_resume(self):
        self.write({'state': 'progress'})
