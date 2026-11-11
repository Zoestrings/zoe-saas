import asyncio
from zoe.settings import load_project_secrets
from zoe.telegram.adapter import PTBTelegramAdapter
import sqlite3

async def main():
    conn = sqlite3.connect('data/operational/operational.db')
    cur = conn.cursor()
    cur.execute('SELECT last_persisted_update_id, next_offset FROM polling_state WHERE project_id = ?', ('live_test',))
    print('DB polling state:', cur.fetchone())
    
    cur.execute('SELECT id, telegram_update_id, group_id, telegram_message_id, text, state, decision, decision_reason, created_at FROM inbox_messages ORDER BY id DESC LIMIT 10')
    print('Recent inbox messages:')
    for row in cur.fetchall():
        print(row)
        
    cur.execute('SELECT id, group_id, text, state, sent_at FROM outbox_messages ORDER BY id DESC LIMIT 5')
    print('Recent outbox messages:')
    for row in cur.fetchall():
        print(row)

if __name__ == '__main__':
    asyncio.run(main())
