# See LICENSE file for full copyright and licensing details.

{
    'name': 'Whatsapp POS',
    'version': '14.0.0.1.0',
    'license': 'OPL-1',
    'author': "Alphasoft",
    'sequence': 1,
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'summary': 'This module is used for Whatsapp Point of Sales',
    'category': 'Extra Tools',
    'depends': ['base_automation', 'point_of_sale', 'aos_whatsapp'],
    'data': [
        'data/pos_data.xml',
        #'report/report_invoice.xml',
        #'report/point_of_sale_report.xml',
        'views/pos_order_view.xml',
        'views/pos_config_view.xml',
        'views/templates.xml',
        #'wizard/whatsapp_compose_view.xml',
    ],
    'external_dependencies': {'python': ['html2text']},
    'qweb': [
        'static/src/xml/mobile_widget.xml',
        'static/src/xml/pos_whatsapp.xml',
        'static/src/xml/pos_order_list.xml',
        'static/src/xml/pos_order_reprint.xml',
        'static/src/xml/ClientListScreen/ClientLine.xml',
        'static/src/xml/ClientListScreen/ClientDetailsEdit.xml',
        'static/src/xml/ClientListScreen/ClientListScreen.xml',
    ],

    'demo': [],
    'test': [],
    'css': [],
    'js': [],
    'price': 0,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
