# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    mrp_id = fields.Many2one('mrp.production')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_raw_material = fields.Boolean(string='Is Raw Material', default=False)

    @api.constrains('name', 'micron', 'size', 'categ_id')
    def constrain_product_check(self):
        for rec in self:
            prod_id = self.env['product.template'].search([('name', '=', rec.name), ('micron', '=', rec.micron), ('size', '=', rec.size), ('categ_id', '=', rec.categ_id.id)]) - rec
            if prod_id:
                raise ValidationError(_('Same Product already exist in this System, Please check again!'))

    @api.model
    def default_get(self, vals):
        res = super(ProductTemplate, self).default_get(vals)
        res['detailed_type'] = 'product'
        return res