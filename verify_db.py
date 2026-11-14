import sqlite3
conn = sqlite3.connect(r'C:\Users\windows11\AppData\Local\GlobalAirdropHunter\app.db')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
print('Integrity:', cursor.fetchone()[0])
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:')
for t in tables:
    print('  -', t[0])
cursor.execute('SELECT COUNT(*) FROM campaigns')
print('Campaigns:', cursor.fetchone()[0])
conn.close()