import os
import sys
sys.path.insert(0, r'D:\Py\qhun22')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [t[0] for t in cursor.fetchall()]
print('Tables:', tables)
print('Has store_sitevisit:', 'store_sitevisit' in tables)
