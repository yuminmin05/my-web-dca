import sqlite3
import os
from decimal import Decimal

path = os.path.join(os.getcwd(), 'db.sqlite3')
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute('SELECT rowid, final_portfolio_value, monthly_investment, target_amount FROM dashboard_garesultsnapshot')
rows = cur.fetchall()
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
            conn.close()
            raise
print('no invalid decimal values found')
conn.close()
