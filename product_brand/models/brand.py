# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError

class product_brand(models.Model):
    _name = 'product.brand'

    name = fields.Char("Brand Name")
    code = fields.Char()
    # product_template_ids = fields.One2many('product.template', 'brand_id', 'Products')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_brand(self):
        product_data = self.env['product.product'].search([('brand_id', 'in', self.ids)], limit=1)
        if product_data:
            raise ValidationError(
                _('You are Not Able To Delete Brand .There is Brand Set In  Product.'))

