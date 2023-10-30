from odoo import http
from odoo.http import request


class PosWhatsAppController(http.Controller):

    @http.route('/pos/send_whatsapp_message', type='json', auth='none')
    def send_whatsapp_message(self, order_id):
        pos_order = request.env['pos.order'].browse(int(order_id))
        if pos_order:
            message = "Your order is confirmed. Order ID: {}".format(pos_order.name)
            pos_order.send_whatsapp_message(message)
            return {'success': True}
        else:
            return {'success': False, 'error': 'Order not found'}
