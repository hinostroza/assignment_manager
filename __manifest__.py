{
    'name': "Product Assignment Management",
    'version': '1.0',
    'summary': "Module to manage the assignment of warehouse products to contacts.",
    'description': """
        This module allows users to assign products from a warehouse to specific contacts.
        It manages inventory movement, automatically deducting stock
        when a product is assigned to a contact. It also provides a detailed
        view of all movements made.
    """,
    'author': "Carlos Hinostroza",
    'website': "http://www.transglobal.pe",
    'category': 'Productivity',
    'depends': ['base', 'stock'],
    'data': [
        # Aquí se agregarán los archivos XML y de seguridad
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/report_actions.xml',
        'views/assignment_report_templates.xml',
        'views/assignment_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}