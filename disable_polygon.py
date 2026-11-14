import sys
import os
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

os.environ['DATABASE_PATH'] = r'C:\Users\windows11\AppData\Local\GlobalAirdropHunter\app.db'

from backend.database.connection import get_db

conn = get_db()

# Disable Polygon blog (RSS parse error)
conn.execute('UPDATE sources SET enabled = 0, status = ? WHERE id = ?', ('disabled', 'rss-polygon-blog'))
print('Disabled: rss-polygon-blog')

conn.commit()
print('Done')