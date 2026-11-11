import asyncio
from zoe.settings import load_project_secrets
from zoe.telegram.adapter import PTBTelegramAdapter

async def main():
    sec = load_project_secrets('live_test')
    adapter = PTBTelegramAdapter(sec['bot_token'])
    chat = await adapter._bot.get_chat('-5214407126')
    print('Chat title:', chat.title)
    print('Chat type:', chat.type)
    print('Chat id:', chat.id)

if __name__ == '__main__':
    asyncio.run(main())

