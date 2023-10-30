import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(">>> Birhah Whatsapp Integration <<<")


class BirhahWhatsappController(http.Controller):

    @http.route('/callback/webhook', type='json', auth='none')
    def callback_webhook(self, **kwargs):
        _logger.info(f"Webhook Response : {kwargs}")
        return kwargs
