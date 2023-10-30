# -*- coding: utf-8 -*-
import logging
import pytz

import requests
import json
import base64
from odoo import api, fields, models, _, sql_db, tools
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import AccessError, UserError, ValidationError

import html2text
from odoo.addons.aos_whatsapp.klikapi import texttohtml
_logger = logging.getLogger(__name__)


class POSOrder(models.Model):
    _inherit = 'pos.order'
    
    whatsapp_sent = fields.Boolean('Whatsapp Sent')

    def _get_default_whatsapp_recipients(self):
        return []
    
    def _formatting_mobile_number(self, partner, whatsapp):
        module_rec = self.env['ir.module.module'].sudo().search_count([
            ('name', '=', 'crm_phone_validation'),
            ('state', '=', 'installed')])
        country_code = str(partner.country_id.phone_code) if partner.country_id else str(self.company_id.country_id.phone_code)
        return module_rec and re.sub("[^0-9]", '', whatsapp) or \
            country_code + whatsapp[1:] if whatsapp[0] == '0' else country_code + whatsapp
                    
    # def _get_whatsapp_server(self):
    #     WhatsappServer = self.env['ir.whatsapp_server']
    #     whatsapp_ids = WhatsappServer.search([('status','=','authenticated')], order='sequence asc')
    #     if len(whatsapp_ids) == 1:
    #         return whatsapp_ids
    #     return False
    
    def _prepare_mail_message(self, author_id, chat_id, record, model, body, data, subject, partner_ids, attachment_ids, response, status):
        values = {
            'author_id': author_id,
            'model': model or 'res.partner',
            'res_id': record,#model and self.ids[0] or False,
            'body': body,
            'whatsapp_data': data,
            'subject': subject or False,
            'message_type': 'whatsapp',
            'record_name': subject,
            'partner_ids': [(4, pid) for pid in partner_ids],
            'attachment_ids': attachment_ids and [(6, 0, attachment_ids.ids)],
            'whatsapp_method': data['method'],
            'whatsapp_chat_id': chat_id,
            'whatsapp_response': response,
            'whatsapp_status': status,
        }
        return values
    
    def action_send_whatsapp_to_customer(self, name, client, ticket):
        #print ('==action_whatsapp_to_customer=',self._context.get('receipt_data'))
        if not self:
            return False
        if not client.get('whatsapp'):
            return False
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        message = client['message']
        MailMessage = self.env['mail.message']
        get_version = self.env["ir.module.module"].sudo().search([('name','=','base')], limit=1).latest_version
        #message = _("Dear *%s*, Here is your electronic ticket for the %s.") % (client['name'], name)
        #print ('===message===',self.config_id, name, client, message)
        #ticket = self._context.get('receipt_data')
        if self.config_id.whatsapp_server_id and self.config_id.whatsapp_server_id.status == 'authenticated':
            #if whatsapp_server.status == 'authenticated':
            #print ('===message===',self._get_whatsapp_server().status)
            KlikApi = self.config_id.whatsapp_server_id.klikapi()      
            KlikApi.auth()   
            attachment_ids = []
            chatIDs = []
            message_data = {}
            send_message = {}
            status = 'error'
            #partners = self.env['res.partner'].browse(client['id'])
            # if client['id']:
            #     partners = client['id']
                # if client['order'].partner_id.child_ids:
                #     #ADDED CHILD FROM PARTNER
                #     for partner in client['order'].partner_id.child_ids:
                #         partners += partner
            filename = 'Receipt-' + name + '.jpg'
            attachment = self.env['ir.attachment'].search([('store_fname','=',filename)])
            #print ('==attachment=11=',ticket[:15])
            if not attachment:
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': ticket,
                    'res_model': 'pos.order',
                    'res_id': self.ids[0],
                    'store_fname': filename,
                    'mimetype': 'image/jpeg',
                })
            message_attach = {
                'method': 'sendFile',
                #'phone': whatsapp,
                'body': 'data:image/jpeg;base64,' + str(attachment.datas.decode("utf-8")),
                'filename': filename,
                'caption': message,#att['filename'],
                'get_version': get_version,
            }
            if not client['order']['client'] and client['whatsapp']:
                #print ('no-customer--')
                whatsapp = client['whatsapp']
                message_attach.update({'phone': whatsapp})
                data_attach = json.dumps(message_attach)
                send_attach = KlikApi.post_request(method='sendFile', data=data_attach)
                #print ('==attachment=33=',send_attach)
                if send_attach.get('message')['sent']:
                    status = 'send'
                    self.whatsapp_sent = True
                    _logger.warning('Success to send Message to WhatsApp number %s', client['whatsapp'])
                else:
                    status = 'error'
                    _logger.warning('Failed to send Message to WhatsApp number %s', client['whatsapp'])
                chatID = None
                vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID, self.id, 'pos.order', texttohtml.formatHtml(message.replace('\xa0', ' ')), message_attach, name, [], [], send_attach, status)
                MailMessage.sudo().create(vals)
                new_cr.commit()
            if client['order']['client']:
                partner = self.env['res.partner'].browse(client['order']['client']['id'])
                if partner.country_id and (client['whatsapp'] or partner.whatsapp):
                    #SEND MESSAGE
                    whatsapp = self._formatting_mobile_number(partner, client['whatsapp'])
                    message_attach.update({'phone': whatsapp})
                    data_attach = json.dumps(message_attach)
                    send_attach = KlikApi.post_request(method='sendFile', data=data_attach)
                    #print ('==attachment=33=',send_attach)
                    if send_attach.get('message')['sent']:
                        partner.sudo().whatsapp = client['whatsapp']
                        status = 'send'
                        self.whatsapp_sent = True
                        _logger.warning('Success to send Message to WhatsApp number %s', whatsapp)
                    else:
                        status = 'error'
                        _logger.warning('Failed to send Message to WhatsApp number %s', whatsapp)
                    chatID = None
                    vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID, self.id, 'pos.order', texttohtml.formatHtml(message.replace('_PARTNER_', self.partner_id.name).replace('\xa0', ' ')), message_attach, name, [partner.id], [], send_attach, status)
                    MailMessage.sudo().create(vals)
                    new_cr.commit()
        else:
            _logger.error('Could not sent whatsapp the POS Order')
        return
    
    def action_resend_whatsapp_to_customer(self, name, client, ticket):
        #print ('==action_whatsapp_to_customer=',self._context.get('receipt_data'))
        if not self:
            return False
        if not client.get('whatsapp'):
            return False
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        message = client['message']
        MailMessage = self.env['mail.message']
        get_version = self.env["ir.module.module"].sudo().search([('name','=','base')], limit=1).latest_version
        #message = _("Dear *%s*, Here is your electronic ticket for the %s.") % (client['name'], name)
        #print ('===message===',self.config_id, name, client, message)
        config = self.env['pos.config'].browse(int(client.get('config_id')))
        order = self.env['pos.order'].browse(int(client.get('order_id')))
        #ticket = self._context.get('receipt_data')
        if config.whatsapp_server_id and config.whatsapp_server_id.status == 'authenticated':
            #if whatsapp_server.status == 'authenticated':
            #print ('===message===',self._get_whatsapp_server().status)
            KlikApi = config.whatsapp_server_id.klikapi()      
            KlikApi.auth()   
            attachment_ids = []
            chatIDs = []
            message_data = {}
            send_message = {}
            status = 'error'
            #partners = self.env['res.partner'].browse(client['id'])
            # if client['id']:
            #     partners = client['id']
                # if client['order'].partner_id.child_ids:
                #     #ADDED CHILD FROM PARTNER
                #     for partner in client['order'].partner_id.child_ids:
                #         partners += partner
            filename = 'Receipt-' + name + '.jpg'
            attachment = self.env['ir.attachment'].search([('store_fname','=',filename)])
            #print ('==attachment=11=',attachment)
            if not attachment:
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': ticket,
                    'res_model': 'pos.order',
                    'res_id': order.id,
                    'store_fname': filename,
                    'mimetype': 'image/jpeg',
                })
            message_attach = {
                'method': 'sendFile',
                #'phone': whatsapp,
                'body': 'data:image/jpeg;base64,' + str(attachment.datas.decode("utf-8")),
                'filename': filename,
                'caption': message,#att['filename'],
                'get_version': get_version,
            }
            if not order.partner_id and client['whatsapp']:
                #print ('no-customer--')
                whatsapp = client['whatsapp']
                message_attach.update({'phone': whatsapp})
                data_attach = json.dumps(message_attach)
                send_attach = KlikApi.post_request(method='sendFile', data=data_attach)
                #print ('==attachment=33=',send_attach)
                if send_attach.get('message')['sent']:
                    status = 'send'
                    order.whatsapp_sent = True
                    _logger.warning('Success to send Message to WhatsApp number %s', client['whatsapp'])
                else:
                    status = 'error'
                    _logger.warning('Failed to send Message to WhatsApp number %s', client['whatsapp'])
                chatID = None
                vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID, order.id, 'pos.order', texttohtml.formatHtml(message.replace('\xa0', ' ')), message_attach, name, [], [], send_attach, status)
                MailMessage.sudo().create(vals)
                new_cr.commit()
            if order.partner_id:
                partner = order.partner_id#self.env['res.partner'].browse(client['order']['client']['id'])
                if partner.country_id and (client['whatsapp'] or partner.whatsapp):
                    #SEND MESSAGE
                    whatsapp = order._formatting_mobile_number(partner, client['whatsapp'])
                    message_attach.update({'phone': whatsapp})
                    data_attach = json.dumps(message_attach)
                    send_attach = KlikApi.post_request(method='sendFile', data=data_attach)
                    #print ('==attachment=33=',send_attach)
                    if send_attach.get('message')['sent']:
                        partner.whatsapp = client['whatsapp']
                        status = 'send'
                        order.whatsapp_sent = True
                        _logger.warning('Success to send Message to WhatsApp number %s', whatsapp)
                    else:
                        status = 'error'
                        _logger.warning('Failed to send Message to WhatsApp number %s', whatsapp)
                    chatID = None
                    vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID, order.id, 'pos.order', texttohtml.formatHtml(message.replace('_PARTNER_', order.partner_id.name).replace('\xa0', ' ')), message_attach, name, [partner.id], [], send_attach, status)
                    MailMessage.sudo().create(vals)
                    new_cr.commit()
        else:
            _logger.error('Could not sent whatsapp the POS Order')
        return
    
    def print_pos_receipt(self):
        orderlines = []
        paymentlines = []
        discount = 0

        for orderline in self.lines:
            new_vals = {
                'product_id': orderline.product_id.name,
                'total_price' : orderline.price_subtotal_incl,
                'qty': orderline.qty,
                'price_unit': orderline.price_unit,
                'discount': orderline.discount,
                }
                
            discount += (orderline.price_unit * orderline.qty * orderline.discount) / 100
            orderlines.append(new_vals)

        for payment in self.payment_ids:
            if payment.amount > 0:
                temp = {
                    'amount': payment.amount,
                    'name': payment.payment_method_id.name
                }
                paymentlines.append(temp)
        tz = pytz.timezone(self.user_id.tz or 'UTC')
        vals = {
            'config_id': self.config_id.id,
            'order_id': self.id,
            'client': self.partner_id,
            'client_name': self.partner_id.name,
            'client_whatsapp': self.partner_id.whatsapp,
            'discount': discount,
            'orderlines': orderlines,
            'paymentlines': paymentlines,
            'change': self.amount_return,
            'subtotal': self.amount_total - self.amount_tax,
            'tax': self.amount_tax,
            'user_name' : self.user_id.name,
            'date_order':self.date_order.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S"),
            # 'loyalty': self.config_id.loyalty_id,
            # 'loyalty_name': self.config_id.loyalty_id.name,
            # 'loyalty_points': self.loyalty_points,
            #'barcode': self.barcode,
        }
        #print ('==vals==',vals)
        return vals
