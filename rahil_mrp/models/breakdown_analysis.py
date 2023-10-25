# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class BreakdownReasons(models.Model):
    _name = 'breakdown.reason'
    _rec_name = 'name'

    name = fields.Char('Reason')


class BreakdownAnalysis(models.Model):
    _name = 'breakdown.analysis'

    # breakdown_reason = fields.Many2many('breakdown.reason', string='Breakdown Reasons')
    breakdown_reason = fields.Char(string='Breakdown Reasons')
    from_time = fields.Float('From Time')
    to_time = fields.Float('To Time')
    total_hours = fields.Float('Total Hours', compute='compute_total_hours')
    remark = fields.Text('Remark')
    work_id = fields.Many2one('mrp.work')

    @api.depends('from_time', 'to_time')
    def compute_total_hours(self):
        """compute total hours from from_time and to_time time"""
        for rec in self:
            rec.total_hours = rec.to_time - rec.from_time
