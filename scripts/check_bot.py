import asyncio
import json
from zoe.settings import load_project_secrets, load_project_config
from zoe.telegram.adapter import PTBTelegramAdapter

async def test():
    secrets = load_project_secrets('live_test')
    config = load_project_config('live_test')
    token = secrets.get('bot_token')
    adapter = PTBTelegramAdapter(bot_token=token)
    me = await adapter.get_me()
    print('Bot user:', me)
    print('Configured group:', config.get('telegram', {}).get('group_id'))
    updates = await adapter.get_updates(offset=None, timeout=2)
    print('Number of updates returned:', len(updates))
    for u in updates[-5:]:
        print('Update:', u)

if __name__ == '__main__':
    asyncio.run(test())

