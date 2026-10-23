import asyncio
import base64
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import storage
from .engine import Engine
from .bot import Telegram
from .provider import validate_symbol
from .access import access_control, settings
from .charts import ChartPhoto

engine=Engine();bot=Telegram(engine);engine.bot=bot
@asynccontextmanager
async def lifespan(app):
    settings()
    tasks=[asyncio.create_task(engine.loop()),asyncio.create_task(bot.loop())]
    if hasattr(engine.provider,'start_stream'):
        tasks.append(asyncio.create_task(engine.provider.start_stream()))
    yield
    for t in tasks:t.cancel()
    await asyncio.gather(*tasks,return_exceptions=True)
    await engine.provider.close();await bot.client.aclose()

app=FastAPI(title='Fintech Bot BT1',lifespan=lifespan)
@app.middleware('http')
async def local_only(request,call_next):
    return await access_control(request,call_next)
@app.get('/healthz')
def health():
    return {'ok':True}
@app.exception_handler(ValueError)
async def value_error(request,e):return JSONResponse({'detail':str(e)},status_code=400)
@app.get('/api/status')
def status():
    return dict(provider=getattr(engine.provider,'source',engine.provider.__class__.__name__),provider_error=engine.provider_error,stream_connected=bool(getattr(engine.provider,'_stream_started',False)),scanning=engine.scanning,last_scan=engine.last_scan,errors=engine.errors,watchlist=engine.watchlist,
        market_universe=engine.market_universe,market_scan_complete=engine.universe_complete,
        scan_progress={'done':engine.scan_done,'total':engine.scan_total},
        signals=list(engine.signals.values()),telegram=dict(connected=bool(bot.username),username=bot.username,error=bot.error,chats=storage.chats()),interval=900)
@app.get('/api/stock/{symbol}')
async def stock(symbol:str):return await engine.analyze(symbol)
@app.get('/api/backtest/{symbol}')
async def test(symbol:str,months:int=6):
    if months not in (3,6):raise ValueError('Chỉ hỗ trợ 3 hoặc 6 tháng.')
    return await engine.test(symbol,months)
@app.post('/api/scan')
async def scan():
    if not engine.scanning:asyncio.create_task(engine.scan())
    return {'ok':True}
class Watch(BaseModel):symbols:list[str]=Field(min_length=1,max_length=15)
@app.post('/api/watchlist')
async def watch(body:Watch):
    engine.watchlist=list(dict.fromkeys(validate_symbol(s) for s in body.symbols));storage.put('watchlist',engine.watchlist)
    engine.signals={k:v for k,v in engine.signals.items() if k in engine.watchlist}
    return {'ok':True}
class Token(BaseModel):token:str=Field(min_length=25,max_length=200)
@app.post('/api/telegram/connect')
async def connect(body:Token):return await bot.connect(body.token.strip())
class Command(BaseModel):text:str=Field(max_length=500)
@app.post('/api/demo')
async def demo(body:Command):
    reply=await bot.command(body.text)
    if isinstance(reply,ChartPhoto):
        return {'reply':reply.caption,'image':'data:image/png;base64,'+base64.b64encode(reply.png).decode('ascii')}
    return {'reply':reply}
class Chat(BaseModel):chat_id:int
@app.post('/api/telegram/test')
async def test_message(body:Chat):
    if body.chat_id not in [c['chat_id'] for c in storage.chats()]:raise ValueError('Mở bot và gửi /start trước.')
    await bot.send(body.chat_id,'✅ Fintech Bot đã kết nối. Gõ /help để xem các lệnh, /subscribe để bật tín hiệu tự động.')
    return {'ok':True}
@app.get('/')
def index():return FileResponse(storage.ROOT/'static/index.html')
app.mount('/static',StaticFiles(directory=storage.ROOT/'static'),name='static')
