"""PythonAnywhere WSGI - samweli20.pythonanywhere.com
File location on PA: /var/www/samweli20_pythonanywhere_com_wsgi.py
Copy the CONTENT below into that file via Web tab.
"""
import os
import sys

path = '/home/samweli20/morgihome'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'morgihome_backend.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
