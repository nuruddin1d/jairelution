# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import models, fields, _, api
import pytz
from odoo.tools.float_utils import float_compare, float_is_zero


class MrpWork(models.Model):
    _name = 'mrp.work'
    _rec_name = 'line_operator'
    _order = 'id desc'
    _inherit = ["mail.thread", "mail.activity.mixin", 'utm.mixin']

    def default_get(self, fields):
        """ default get Shift value as per day and night (A or B)"""
        res = super().default_get(fields)
        res['date'] = datetime.now()
        date = res['date'].astimezone(pytz.timezone('Asia/Kolkata'))
        hour = date.hour
        if hour > 12:
            res['shift'] = 'b'
        else:
            res['shift'] = 'a'
        return res

    line_operator = fields.Many2one('hr.employee', string='Line Operator', required=True)
    # verified_by = fields.Many2one('hr.employee', string='Verified By')
    cast_line_no = fields.Selection([('line1', 'Line 1'), ('line2', 'Line 2')])
    date = fields.Datetime('Date')
    shift = fields.Selection([('a', 'A'), ('b', 'B')], required=True)
    work_line_ids = fields.One2many('mrp.work.line', 'work_id', string='work Lines')
    total_production = fields.Float('Total Production', compute='compute_work_totals')
    total_wastage = fields.Float('Total Wastage', compute='compute_work_totals')
    wastage_reason = fields.Text('Wastage Reason')
    total_breakdown = fields.Float('Total Breakdown Hours/Minutes', compute='compute_work_totals')
    breakdown_analysis_ids = fields.One2many('breakdown.analysis', 'work_id', string="Breakdown Analysis")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')
    mrp_order = fields.Many2one('mrp.production', string='Manufacturing Order', required=True)
    product_id = fields.Many2one(related='mrp_order.product_id')
    product_tracking = fields.Selection(related='product_id.tracking')
    slitter_line = fields.Selection([('line1', 'Line 1'), ('line2', 'Line 2'), ('line3', 'Line 3')])
    work_type = fields.Selection([('cast', 'Cast'), ('slit', 'Slit'), ('mate', 'Mate'), ('rewind', 'Rewind')],
                                 default='cast')

    # @api.model
    # def create(self, vals):
    #     vals = {
    #         'work_type': self.mrp_order.work_order_type if self.mrp_order else 'cast',
    #     }
    #     return super(MrpWork, self).create(vals)
    #
    # def write(self, vals):
    #     vals = {
    #         'work_type': self.mrp_order.work_order_type if self.mrp_order else 'cast',
    #     }
    #     return super(MrpWork, self).write(vals)

    @api.depends('work_line_ids.net_weight', 'work_line_ids.wastage', 'breakdown_analysis_ids.total_hours')
    def compute_work_totals(self):
        """get total production and total wastage from the work line"""
        for rec in self:
            net_weight = 0
            wastage = 0
            hours = 0
            for line in rec.work_line_ids:
                net_weight += line.net_weight
                wastage += line.wastage
            for break_line in rec.breakdown_analysis_ids:
                hours += break_line.total_hours
            rec.total_production = net_weight
            rec.total_wastage = wastage
            rec.total_breakdown = hours

    def action_set_to_confirm(self):
        """ This method is used to change the state to confirm """
        self.ensure_one()
        for rec in self:
            # for line in rec.work_line_ids.filtered(lambda x:x.qc_status in ['draft', 'hold', 'reject']):
            #     if line:
            #         raise ValidationError('One of your work line quality check pending, Please check again')
            # if rec.mrp_order and rec.total_production > 0:
            #     rec.mrp_order.qty_producing += rec.total_production

            rec.write({"state": "confirm"})

    def action_set_to_draft(self):
        """ This method is used to change the state to draft """
        for rec in self:
            # if rec.work_line_ids:
            #     for line in rec.work_line_ids:
            #         line.write({'qc_status': 'draft'})
            rec.write({"state": "draft"})

    # def action_set_to_verified(self):
    #     """ This method is used to change the state to verified and set verified user """
    #     self.verified_by = self.env.user.employee_id.id
    #     self.write({"state": "verified"})

    def unlink(self):
        if self.state == 'confirm':
            raise ValidationError(_("You can't delete confirm Work entry!"))
        return super(MrpWork, self).unlink()


class MrpWorkLine(models.Model):
    _name = 'mrp.work.line'
    _rec_name = 'lot_id'
    _order = 'id desc'
    _inherit = ["mail.thread", "mail.activity.mixin", 'utm.mixin']

    work_id = fields.Many2one('mrp.work')
    mrp_order = fields.Many2one(related='work_id.mrp_order', string='Work Order')
    lot_id = fields.Many2one('stock.production.lot')
    roll_no = fields.Char('Mother Roll No.')
    micron = fields.Integer(related='mrp_order.product_id.micron', string='Micron')
    size = fields.Integer(related='mrp_order.product_id.size', string='Size')
    Type = fields.Many2one(related='mrp_order.product_id.categ_id', string='Type')
    in_time = fields.Float('In Time')
    out_time = fields.Float('Out Time')
    duration = fields.Float('Duration', compute='compute_duration')
    length = fields.Float('Length')
    gross_weight = fields.Float('Gross Weight')
    core_weight = fields.Float('Core Weight')
    net_weight = fields.Float('Net Weight', compute='compute_total_net_weight')
    no_of_tags = fields.Integer('No Of Tags')
    defect_reason = fields.Text('Defect Reason')
    wastage = fields.Float('Wastage(Kgs.)')
    remark = fields.Text('Remarks')
    arm = fields.Integer('ARM')
    no_of_joint = fields.Integer('No. of Joint')
    joint_reason = fields.Text('Joint Reason')
    spot_gsm_ids = fields.Many2many('spot.gsm', 'qc_spot_gsm', string='Spot GSM')
    qc_width = fields.Float('Width(mm)', tracking=True)
    qc_gsm = fields.Float('GSM(g/m2))', tracking=True)
    qc_thickness = fields.Float('Thickness', tracking=True)
    qc_od = fields.Float('OD')
    qc_opacity = fields.Float('opacity(%)', tracking=True)
    qc_treatment_ct = fields.Float('CT', tracking=True)
    qc_treatment_bt = fields.Float('BT', tracking=True)
    qc_sit = fields.Float('SIT', tracking=True)
    qc_sealing_strength = fields.Float('Sealing Strength', tracking=True)
    qc_cof_df = fields.Float('Film to Film (DF)', tracking=True)
    qc_cof_mdf = fields.Float('Film to Metal (DF)', tracking=True)
    qc_tensile_strength_md = fields.Float('MD', tracking=True)
    qc_tensile_strength_td = fields.Float('TD', tracking=True)
    qc_elongation_md = fields.Float('MD', tracking=True)
    qc_elongation_td = fields.Float('TD', tracking=True)
    qc_visual_obs = fields.Boolean('Visual Observation', tracking=True)
    qc_status = fields.Selection([
        ('draft', 'Pending'),
        ('confirm', 'Confirm'),
        ('hold', 'Hold'),
        ('reject', 'Reject'),
    ], string='Status', tracking=True, default='draft')
    qc_remark = fields.Text('Remarks', tracking=True)
    qc_assistant = fields.Many2one('hr.employee', string='QC Assistant', tracking=True)
    qc_product = fields.Many2one(related='work_id.mrp_order.product_id', string='Product', tracking=True)
    qc_shift = fields.Selection([('a', 'A'), ('b', 'B')], tracking=True)
    qc_date = fields.Datetime('Date', tracking=True)
    product_core = fields.Char(string='Core')
    sale_ct = fields.Char(string='CT')
    sale_cof = fields.Char(string='COF')
    roll_od = fields.Char(string='Roll OD')
    qc_wvtr = fields.Char(string='WVTR')
    qc_metal_bond_strength = fields.Char(string='Metal Bond Strength')
    qc_otr = fields.Char(string='OTR')
    include_extra_parameters = fields.Boolean(string='Include Extra Parameters')
    order_ids = fields.Many2many('sale.order', string='Sale Orders')
    order_id = fields.Many2one('sale.order', string='Sale Order', domain="[('id', 'in', order_ids)]")
    work_type = fields.Selection(related="work_id.work_type")
    # quality_check_id = fields.One2many('quality.control','work_line','Quality Analysis')

    def generate_lot_number(self):
        """This method create lot sequence for mrp from work entry"""
        self.ensure_one()
        lot_obj = self.env['stock.production.lot']
        if self.mrp_order:
            work_type = self.work_id.work_type
            year = str(datetime.now().year % 100)
            day = str(datetime.now().strftime('%d'))
            month = str(datetime.now().strftime('%m'))
            lot_id = False
            name = False
            pre_roll = False
            if work_type in ['rewind', 'mate', 'slit']:
                for line in self.mrp_order.move_raw_ids:
                    if line[0].move_line_ids:
                        pre_roll = line[0].move_line_ids[0].lot_id if line[0].move_line_ids[0].lot_id else False
                        sli_str = pre_roll.name
                        lot_id = sli_str[2:6] if sli_str else False
            if work_type == 'cast':
                name = year + str(self.env['ir.sequence'].next_by_code('stock.production.lot') or '/') + 'J'
            elif work_type == 'rewind':
                name = year + lot_id + 'R'
            elif work_type == 'mate':
                name = year + lot_id + 'M'
            elif work_type == 'slit':
                qc = self.env['quality.control'].search([('is_qc','=',True)])

                list = []
                if qc:
                    for rec in qc:
                        vals = {
                            'properties': rec.id,
                            'ref': rec.ref,
                            'test_parameter': rec.test_parameter.id,
                            'unit': rec.unit
                        }
                        list.append(vals)
                    qc_test = self.env['quality.control.test'].create(list)


                self.quality_checks_id = [(6, 0,qc_test.ids)]


                if pre_roll:
                    name = year + day + month + lot_id + str(pre_roll.roll_count).zfill(2)
                    pre_roll.roll_count += 1
            exiting_lot_id = lot_obj.search([('name', '=', name)])
            if exiting_lot_id:
                self.lot_id = exiting_lot_id.id
            else:
                self.lot_id = lot_obj.create(
                    {'name': name, 'product_id': self.mrp_order.product_id.id, 'company_id': 1, 'micron': self.micron,
                     'type': self.Type.id, 'size': self.size, 'length': self.length, 'gross_weight': self.gross_weight,
                     'no_of_joint': self.no_of_joint, 'work_type': work_type,
                     'product_core': self.product_core,
                     'sale_ct': self.sale_ct,
                     'sale_cof': self.sale_cof,
                     'roll_od': self.roll_od,
                     'order_ids': self.order_ids,
                     'order_id': self.order_id})
            if self.lot_id and work_type == 'mate':
                self.qc_assistant = self.env.user.employee_id.id if self.env.user.employee_id else False
                self.change_shift()
                self.action_set_to_confirm()

    @api.depends('gross_weight', 'core_weight')
    def compute_total_net_weight(self):
        """compute total net weight from gross weight - core weight"""
        for rec in self:
            rec.net_weight = rec.gross_weight - rec.core_weight

    @api.depends('in_time', 'out_time')
    def compute_duration(self):
        """compute total duration from in and out time"""
        for rec in self:
            rec.duration = rec.out_time - rec.in_time

    # def action_set_to_confirm(self):
    #     """ This method is used to change the qc_status to confirm """
    #     self.write({"qc_status": "confirm"})

    def action_set_to_confirm(self):
        """ This method is used to change the qc_status to confirm and direct effect in stock """
        self.write({"qc_status": "confirm"})
        stock_move = self.mrp_order.move_finished_ids.filtered(
            lambda m: m.product_id == self.qc_product and m.state not in (
                'done', 'cancel'))  # search existing move which is not done yet
        if stock_move:
            vals = stock_move._prepare_move_line_vals(quantity=self.net_weight)
            vals.update({'lot_id': self.lot_id.id, 'lot_name': self.lot_id.name, 'qty_done': self.net_weight})
            stock_move_line = self.env['stock.move.line'].create(vals)
            new_move = stock_move[0]
            Quant = self.env['stock.quant']
            rounding = stock_move_line.product_id.uom_id.rounding
            remaining_qty = new_move.product_uom_qty - self.net_weight
            quantity = stock_move_line.product_uom_id._compute_quantity(stock_move_line.qty_done,
                                                                        stock_move_line.move_id.product_id.uom_id,
                                                                        rounding_method='HALF-UP')
            in_date = None
            available_qty, in_date = Quant._update_available_quantity(stock_move_line.product_id,
                                                                      stock_move_line.location_id, -quantity,
                                                                      lot_id=stock_move_line.lot_id)
            if available_qty < 0 and stock_move_line.lot_id:
                untracked_qty = Quant._get_available_quantity(stock_move_line.product_id, stock_move_line.location_id,
                                                              lot_id=False, strict=True)
                if untracked_qty:
                    taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                    Quant._update_available_quantity(stock_move_line.product_id, stock_move_line.location_id,
                                                     -taken_from_untracked_qty, lot_id=False)
                    Quant._update_available_quantity(stock_move_line.product_id, stock_move_line.location_id,
                                                     taken_from_untracked_qty,
                                                     lot_id=stock_move_line.lot_id)
                Quant._update_available_quantity(stock_move_line.product_id, stock_move_line.location_dest_id, quantity,
                                                 lot_id=stock_move_line.lot_id,
                                                 in_date=in_date)
            pre_quants = Quant._gather(stock_move_line.product_id, stock_move_line.location_dest_id,
                                       lot_id=stock_move_line.lot_id)
            # pre_quants_un = Quant._gather(stock_move_line.product_id, stock_move_line.location_dest_id)
            available_quantity = sum(pre_quants.mapped('reserved_quantity'))
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                stock_move._do_unreserve()
            stock_move._action_confirm()
            stock_move._action_assign()
            stock_move_line.write({'qty_done': self.net_weight, 'state': 'done'})
            move_order_lines = new_move._split(remaining_qty)
            self.env['stock.move'].create(move_order_lines)
            new_move.update({'state': 'done'})

            stock_move._action_done()
            self.mrp_order.write(
                {'qty_producing': self.mrp_order.qty_producing + self.net_weight})  # update qty producing
            self.mrp_order._onchange_producing()

    def action_set_to_hold(self):
        """ This method is used to change the qc_status to hold """
        self.write({"qc_status": "hold"})

    def action_set_to_reject(self):
        """ This method is used to change the qc_status to reject """
        self.write({"qc_status": "reject"})

    def action_set_to_recheck(self):
        """ This method is used to change the qc_status to draft """
        self.write({"qc_status": "draft"})

    @api.onchange('qc_assistant')
    def change_shift(self):
        for rec in self:
            rec.qc_date = datetime.today()
            if rec.qc_date:
                date = rec.qc_date.astimezone(pytz.timezone('Asia/Kolkata'))
                hour = date.hour
                if hour > 12:
                    rec.qc_shift = 'b'
                else:
                    rec.qc_shift = 'a'

    def unlink(self):
        for rec in self:
            if rec.qc_status == 'confirm':
                raise ValidationError(_("You can't delete confirm quality check entry!"))
        return super(MrpWorkLine, self).unlink()

    @api.model
    def create(self, vals):
        res = super(MrpWorkLine, self).create(vals)
        if res.mrp_order:
            if res.work_type == 'cast':
                res['product_core'] = res.mrp_order.production_line[0].so_product_core
                res['sale_ct'] = res.mrp_order.production_line[0].so_sale_ct
                res['sale_cof'] = res.mrp_order.production_line[0].so_sale_cof
                res['roll_od'] = res.mrp_order.production_line[0].so_roll_od
                res['order_ids'] = res.mrp_order.order_ids.ids
            else:
                res['product_core'] = res.mrp_order.component_lot_ids[0].product_core
                res['sale_ct'] = res.mrp_order.component_lot_ids[0].sale_ct
                res['sale_cof'] = res.mrp_order.component_lot_ids[0].sale_cof
                res['roll_od'] = res.mrp_order.component_lot_ids[0].roll_od
                res['order_ids'] = res.mrp_order.order_ids.ids
        return res
