import asyncio
from zoe.settings import load_project_secrets
from zoe.telegram.adapter import PTBTelegramAdapter

async def main():
    sec = load_project_secrets('live_test')
    adapter = PTBTelegramAdapter(sec['bot_token'])
    me = await adapter._bot.get_me()
    print('Bot ID:', me.id)
    print('Bot username:', me.username)
    print('Bot first_name:', me.first_name)
    print('Can read all group messages (Privacy Mode off):', me.can_read_all_group_messages)

if __name__ == '__main__':
    asyncio.run(main())

