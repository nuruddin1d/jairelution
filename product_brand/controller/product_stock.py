# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class StockController(http.Controller):

    @http.route(['/stock/artical/'], type='http', auth='public', csrf=False)
    def product_stock(self, **post):
        artical_search = post.get('search')
        products = request.env['product.product'].sudo().search([('default_code', 'ilike', artical_search)])
        for product in products:
            if artical_search:
                if request.env.user.has_group('base.group_user'):
                    quant = request.env['stock.production.lot'].sudo().search([('product_id', 'ilike', product.id)])
                    lot = []
                    for res in quant:
                        lot.append(res.name)
                    return request.render('product_brand.product_stock_check', {
                        'product_stock': product,
                        'lot_id': lot,
                        'user_type': 'internal'
                    })
                elif request.env.user.has_group('base.group_public'):
                    return request.render('product_brand.product_stock_check', {
                        'product_stock': product,
                        'user_tye': 'public'
                    })
            else:
                return request.render('product_brand.product_stock_check', {

                })


class BarcodeProductController(http.Controller):

    @http.route('/product/barcode/<barcode>', type='http', auth='user', website=True)
    def product_details_by_barcode(self, barcode):
        Product = request.env['product.product']
        product = Product.search([('barcode', '=', barcode)], limit=1)

        if not product:
            return ("Enter correct barcode")
        quant = request.env['stock.production.lot'].sudo().search([('product_id', 'ilike', product.id)])
        lot = []
        for res in quant:
            lot.append(res.name)

        return request.render('product_brand.custom_product_template', {'product': product,'lot_id': lot,})

