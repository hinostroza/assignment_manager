{
    'name': "Gestión de Productos por Contacto",
    'version': '1.0',
    'summary': "Módulo para gestionar la asignación de productos de almacén a contactos.",
    'description': """
        Este módulo permite a los usuarios asignar productos de un almacén a contactos específicos.
        Gestiona el movimiento de inventario, descontando automáticamente el stock
        cuando un producto es asignado a un contacto. También proporciona una vista
        detallada de todos los movimientos realizados.
    """,
    'author': "Carlos Hinostroza",
    'website': "http://www.transglobal.pe",
    'category': 'Productivity',
    'depends': ['base', 'stock'],
    'data': [
        # Aquí se agregarán los archivos XML y de seguridad
        'security/ir.model.access.csv',
        'views/assignment_views.xml',
        'data/sequence.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}