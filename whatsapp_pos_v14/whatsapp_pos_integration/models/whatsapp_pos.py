# models.py

from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    whatsapp_message_sent = fields.Boolean('WhatsApp Message Sent', default=False)
    whatsapp_message_id = fields.Char('WhatsApp Message ID')

    def send_whatsapp_message(self, message):
        pass
