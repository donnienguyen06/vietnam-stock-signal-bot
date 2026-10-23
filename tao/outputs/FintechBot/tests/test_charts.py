import asyncio
import base64
from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace

import httpx
from PIL import Image
from fastapi.testclient import TestClient

from fintech.charts import ChartPhoto, create_chart, render_chart, is_doji
from fintech.provider import TZ
from fintech.bot import Telegram


def market():
    end = datetime(2026, 9, 9, tzinfo=TZ)
    bars = [dict(date=(end-timedelta(days=89-i)).date().isoformat(),
        open=20000+i*20, high=20300+i*20, low=19800+i*20, close=20100+i*20,
        volume=1_000_000+i*1000) for i in range(90)]
    return {'bars': bars, 'cached': False}


def test_doji_body_threshold_and_no_trade_exclusion():
    assert is_doji(100, 110, 90, 102, 1000)
    assert is_doji(100, 110, 90, 100, 1000)
    assert not is_doji(100, 110, 90, 103, 1000)
    assert not is_doji(100, 100, 100, 100, 1000)
    assert not is_doji(100, 110, 90, 100, 0)


def test_png_size_and_quoted_timestamp():
    stamp = datetime(2026, 9, 10, 10, 0, tzinfo=TZ)
    p = render_chart('HPG', market(), {'price':22000, 'timestamp':stamp.isoformat()}, stamp)
    assert p.png.startswith(b'\x89PNG\r\n\x1a\n')
    assert len(p.png) < 10_000_000
    im = Image.open(BytesIO(p.png)); assert im.size == (1680, 1120)
    assert '10/09/2026 10:00:00' in p.caption
    assert 'không tự cập nhật' in p.caption
    assert 'Nến Nhật / Doji' in p.caption


def test_invalid_quote_never_shown_as_live():
    stamp = datetime(2026, 9, 10, 10, 0, tzinfo=TZ)
    p = render_chart('VCB', market(), {'price':0, 'timestamp':stamp.isoformat()}, stamp)
    assert 'Không lấy được giá mới nhất' in p.caption


def test_stale_history_and_quote_are_labelled():
    stamp = datetime(2026, 9, 20, 10, 0, tzinfo=TZ)
    data = market(); data['cached'] = True
    p = render_chart('VCB', data, {'price':22000, 'timestamp':'2026-09-09T14:45:00+07:00'}, stamp)
    assert 'cache' in p.caption
    assert 'hơn 15 phút' in p.caption


def test_each_chart_requests_a_fresh_quote(monkeypatch):
    import fintech.charts as charts
    class Provider:
        def __init__(self): self.calls = 0
        async def load(self, symbol): return market()
        async def quote(self, symbol):
            self.calls += 1
            return {'price':self.calls}
    async def scenario():
        provider = Provider()
        engine = SimpleNamespace(provider=provider, symbol_locks={})
        monkeypatch.setattr(charts,'render_chart',lambda symbol,data,quote,at:quote['price'])
        assert await create_chart(engine,'hpg') == 1
        assert await create_chart(engine,'hpg') == 2
    asyncio.run(scenario())


def test_photo_uploaded_as_multipart_to_correct_chat():
    seen = []
    def handle(request):
        seen.append(request)
        return httpx.Response(200,json={'ok':True,'result':{'message_id':1}})
    async def scenario():
        bot = Telegram(None); bot.token='test-token'
        await bot.client.aclose()
        bot.client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        try:
            await bot.send_photo(123,ChartPhoto('HPG',b'PNG-BYTES','Test chart'))
        finally: await bot.client.aclose()
    asyncio.run(scenario())
    assert seen[0].url.path.endswith('/sendPhoto')
    assert 'multipart/form-data' in seen[0].headers['content-type']
    body = seen[0].content
    assert b'123' in body and b'HPG-chart.png' in body and b'PNG-BYTES' in body


def test_chart_placeholder_and_selected_symbol(monkeypatch):
    import fintech.bot as module
    async def fake_chart(engine,symbol):return ChartPhoto(symbol,b'png','caption')
    monkeypatch.setattr(module,'create_chart',fake_chart)
    async def scenario():
        bot=Telegram(None)
        try:
            assert 'Cú pháp' in await bot.command('/chart')
            assert 'Cú pháp' in await bot.command('/chart MÃ_CỔ_PHIẾU')
            result=await bot.command('/chart@ExampleBot vcb')
            assert result.symbol=='VCB'
        finally:await bot.client.aclose()
    asyncio.run(scenario())


def test_dashboard_demo_returns_image(monkeypatch):
    from fintech.app import app, bot
    async def command(text):return ChartPhoto('HPG',b'png','caption')
    monkeypatch.setattr(bot,'command',command)
    r=TestClient(app).post('/api/demo',json={'text':'/chart HPG'})
    assert r.status_code==200
    assert r.json()['image']=='data:image/png;base64,'+base64.b64encode(b'png').decode()
