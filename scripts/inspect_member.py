import asyncio
from zoe.settings import load_project_secrets
from zoe.telegram.adapter import PTBTelegramAdapter

async def main():
    sec = load_project_secrets('live_test')
    adapter = PTBTelegramAdapter(sec['bot_token'])
    member = await adapter._bot.get_chat_member('-5214407126', 8634345016)
    print('Bot member status in -5214407126:', member.status)
    print('Can read messages:', getattr(member, 'can_read_all_group_messages', None))

if __name__ == '__main__':
    asyncio.run(main())

