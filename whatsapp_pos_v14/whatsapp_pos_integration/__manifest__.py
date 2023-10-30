# -*- coding: utf-8 -*-

{
    'name': 'Custom WhatsApp Integration for Odoo POS',
    'version': '14.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Integrate WhatsApp into Odoo POS',
    'author': 'Reliution',
    'depends': ['point_of_sale'],
    'data': [
        # 'views/pos_whatsapp.xml',
        'views/pos_templates.xml',
    ],
    'external_dependencies': {'python': ['html2text']},
    'qweb': [
        'static/src/xml/pos_whatsapp.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'js': [],
    'installable': True,
    'auto_install': False,
}
