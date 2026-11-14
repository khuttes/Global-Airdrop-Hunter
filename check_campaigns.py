import sys
import os
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

os.environ['DATABASE_PATH'] = r'C:\Users\windows11\AppData\Local\GlobalAirdropHunter\app.db'

from backend.database.connection import get_db

conn = get_db()

# Check campaigns
rows = conn.execute('''
    SELECT name, project, type, network, verification_status, risk_level, risk_score, source_id 
    FROM campaigns 
    ORDER BY discovered_at DESC 
    LIMIT 20
''').fetchall()

print('=== RECENT CAMPAIGNS ===')
for r in rows:
    print('  {} | {} | {} | {} | {} | {} | source={}'.format(
        r[0][:50], r[1] or 'N/A', r[2], r[3] or 'N/A', r[4], r[5], r[6], r[7]
    ))

# Count by source
print('\n=== CAMPAIGNS BY SOURCE ===')
rows = conn.execute('''
    SELECT source_id, COUNT(*) as cnt FROM campaigns GROUP BY source_id ORDER BY cnt DESC
''').fetchall()
for r in rows:
    print('  {}: {}'.format(r[0], r[1]))

# Count by type
print('\n=== CAMPAIGNS BY TYPE ===')
rows = conn.execute('SELECT type, COUNT(*) as cnt FROM campaigns GROUP BY type ORDER BY cnt DESC').fetchall()
for r in rows:
    print('  {}: {}'.format(r[0], r[1]))