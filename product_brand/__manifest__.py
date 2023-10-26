# -*- coding: utf-8 -*-
{
    'name': "Product Brand",
    'version': '15.0.0.1',

    'summary': """Assign Brand to products""",

    'description': """
        Categorize your products with brands
    """,

    'author': "Gayatri",
    'website': "http://www.gayatrisales.co.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'l10n_in'],

    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'security/product_security.xml',
        'views/brand_views.xml',
        'views/product_views.xml',
        'views/product_category_views.xml',
        'views/product_stock.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False
}
