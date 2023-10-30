import requests
import logging
from odoo import models, fields

_logger = logging.getLogger(">>> Birhah Whatsapp Integration <<<")


class ResCompany(models.Model):
    _inherit = 'res.company'

    birhah_access_token = fields.Char(string="Access Token")
    birhah_instance_id = fields.Char(string="Instance ID")


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    def action_whatsapp_message(self):
        url = f"https://app.birhah.com/api/send.php?" \
              f"number=918866461261" \
              f"&type=text&message=Hello testing from Odoo" \
              f"&instance_id=6316CF5A9B006" \
              f"&access_token=862b858b12aec508c96095c3479ec44f"
        payload = {}
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        _logger.info(f"Response : {response.text}")
