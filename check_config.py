import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')
from backend.database.connection import get_db
conn = get_db()
row = conn.execute('SELECT id, base_url, config FROM sources WHERE id = ?', ('rss-ethereum-blog',)).fetchone()
if row:
    print('ID:', row[0])
    print('Base URL:', row[1])
    print('Config:', row[2])