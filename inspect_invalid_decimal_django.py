import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dca_system.settings')
import sys
sys.path.insert(0, os.getcwd())

django.setup()
from django.db import connection
from decimal import Decimal

with connection.cursor() as cursor:
    cursor.execute('SELECT rowid, final_portfolio_value, monthly_investment, target_amount FROM dashboard_garesultsnapshot')
    rows = cursor.fetchall()
    print('rowcount', len(rows))
    for row in rows:
        rowid, fp, mi, ta = row
        for field, val in [('final_portfolio_value', fp), ('monthly_investment', mi), ('target_amount', ta)]:
            if val is None:
                continue
            try:
                Decimal(str(val))
            except Exception as e:
                print('bad', rowid, field, repr(val), type(val), e)
                raise
    print('no invalid decimal values found')
