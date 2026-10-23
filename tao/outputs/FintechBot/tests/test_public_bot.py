import asyncio
from fintech.bot import Telegram
from fintech import storage


def test_public_invite_and_independent_subscriptions(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DATA', tmp_path)
    storage.init()

    async def scenario():
        bot = Telegram(None)
        bot.username = 'FintechExampleBot'
        try:
            for cid in [101, 202]:
                storage.chat(cid, 'Người dùng')
                assert 'mọi người' in await bot.command('/start invite', cid)
                await bot.command('/subscribe', cid)
            await bot.command('/unsubscribe', 101)
            states = {c['chat_id']: c['active'] for c in storage.chats()}
            assert states == {101: False, 202: True}
            assert 'https://t.me/FintechExampleBot?start=invite' in await bot.command('/share', 202)
        finally:
            await bot.client.aclose()

    asyncio.run(scenario())
