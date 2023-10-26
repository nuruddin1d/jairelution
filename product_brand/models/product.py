# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import format_amount
import base64
import requests
from datetime import datetime


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one('product.brand', 'Brand')
    lmop = fields.Char(string="LMOP")


    def _construct_tax_string(self, price):
        currency = self.currency_id
        res = self.taxes_id.compute_all(price, product=self, partner=self.env['res.partner'])
        joined = []
        included = round(res['total_included'])
        if currency.compare_amounts(included, price):
            joined.append(_('%s Incl. Taxes', format_amount(self.env, included, currency)))
        excluded = res['total_excluded']
        if currency.compare_amounts(excluded, price):
            joined.append(_('%s Excl. Taxes', format_amount(self.env, excluded, currency)))
        if joined:
            tax_string = f"(= {', '.join(joined)})"
        else:
            tax_string = " "
        return tax_string



class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode = fields.Char(
        'Barcode', copy=False, store=True,
        help="International Article Number used for product identification.")
    mrp= fields.Float('MRP')
    foc_product_id = fields.Many2one('product.product','FOC')
    impo = fields.Char(string="IMPO")

    # @api.onchange('categ_id', 'brand_id')
    # def onchange_product_default_code(self):
    #     for product in self:
    #         if product.categ_id and product.brand_id:
    #             if product.default_code:
    #                 old_code = product.default_code.split('-')[2]
    #                 new_code = product.categ_id.code + '-' + product.brand_id.code
    #                 product.default_code = new_code + '-' + old_code
    #             else:
    #                 code = product.categ_id.code + '-' + product.brand_id.code + '-'
    #                 product.default_code = code

    # @api.depends('categ_id', 'brand_id')
    # def compute_auto_generate_barcode(self):
    #     for rec in self:
    #         if not rec.barcode:
    #             if self.env.company.id == 1:
    #                 rec.barcode = "22" + str(rec.id).zfill(6)
    #             else:
    #                 rec.barcode = "88" + str(rec.id).zfill(6)

    @api.model
    def create(self, vals):
        if 'barcode' not in vals or not vals['barcode']:
            if self.env.company.id == 1:
                vals['barcode'] = self.env['ir.sequence'].next_by_code('product.product.est')
            else:
                vals['barcode'] = self.env['ir.sequence'].next_by_code('product.product.gs')
        return super(ProductProduct, self).create(vals)
