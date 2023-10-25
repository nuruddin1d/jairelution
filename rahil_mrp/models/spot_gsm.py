# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class SpotGsm(models.Model):
    _name = 'spot.gsm'
    _rec_name = 'readings'

    work_line_ids = fields.Many2one('mrp.work.line')
    readings = fields.Float('GSM Readings')

    _sql_constraints = [
        ('readings_name_uniq', 'unique(readings)', 'Readings is already exists !'),
    ]