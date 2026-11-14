import sys
import os
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

os.environ['DATABASE_PATH'] = r'C:\Users\windows11\AppData\Local\GlobalAirdropHunter\app.db'

from backend.database.connection import get_db

conn = get_db()

# Disable test sources (Health Test Source and Arbitrum Blog)
test_source_ids = [
    '060d471e-02ff-46a6-8a7a-2d4beaf7379a',
    '1aad4de3-eedf-40f0-b23f-11064f02dd61', 
    '1cf7b571-5796-4db0-bf93-9a5885882741',
    '42b1570a-a5ea-439b-bd2a-b0c94e2485aa',
    '9a3c4e2c-56f5-4bfc-99d9-8668f659bad5',
    'd3a1beec-3050-49bc-a2bd-f4d0dbee9c25',
    '7af6a8fd-7fbc-4a48-a40d-ec8d33813bb0',  # Arbitrum Blog
]

for sid in test_source_ids:
    conn.execute('UPDATE sources SET enabled = 0, status = ? WHERE id = ?', ('disabled', sid))
    print('Disabled:', sid)

conn.commit()
print('Done')