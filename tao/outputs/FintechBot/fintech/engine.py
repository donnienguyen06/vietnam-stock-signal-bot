import asyncio
from datetime import datetime
from .provider import SYMBOLS, now, validate_symbol
from .ssi_provider import SSI, configured as ssi_configured
from .strategy import signal, backtest
from . import storage

class Engine:
    def __init__(self):
        self.provider=SSI()
        self.provider_error=None if ssi_configured() else 'Chưa điền SSI_CONSUMER_ID và SSI_CONSUMER_SECRET trong .env.'
        self.signals={};self.errors={};self.last_scan=None;self.scanning=False
        self.watchlist=[];self.market_universe=[]
        self.scan_total=0;self.scan_done=0;self.universe_complete=False;self.lock=asyncio.Lock();self.symbol_locks={};self.bot=None
    async def analyze(self,symbol,force=False):
        symbol=validate_symbol(symbol)
        async with self.symbol_locks.setdefault(symbol,asyncio.Lock()):
            data=await self.provider.load(symbol,force)
        s=signal(data['bars'],data['fundamentals']);age=(now().date()-datetime.fromisoformat(s['date']).date()).days
        s.update(symbol=symbol,name=SYMBOLS.get(symbol,symbol),fundamentals=data['fundamentals'],quote=data['quote'],
            fetched_at=data['fetched_at'],source=data['source'],cached=data['cached'],error=data['error'],stale=age>4)
        if symbol in self.watchlist:self.signals[symbol]=s
        return s
    async def scan(self):
        if self.scanning:return
        self.scanning=True
        self.scan_done=0;self.scan_total=0
        try:
            self.market_universe=await self.provider.universe()
            self.universe_complete=len(self.market_universe)>=100
            # Only the SSI-discovered universe is eligible for the market scan.
            if self.market_universe:
                self.watchlist=self.market_universe;storage.put('watchlist',self.watchlist)
            symbols=list(self.watchlist);self.scan_total=len(symbols);self.scan_done=0
            semaphore=asyncio.Semaphore(6)
            async def one(symbol):
                async with semaphore:
                    try:await self.analyze(symbol,True);self.errors.pop(symbol,None)
                    except Exception as e:
                        self.signals.pop(symbol,None)
                        self.errors[symbol]=str(e) if isinstance(e,ValueError) else 'Không xử lý được dữ liệu mã này.'
                    finally:self.scan_done+=1
            await asyncio.gather(*(one(symbol) for symbol in symbols))
            self.last_scan=now().isoformat()
            self.provider_error=None
            if self.bot:await self.bot.alerts(list(self.signals.values()))
        except Exception as exc:
            self.universe_complete=False
            detail=str(exc) if isinstance(exc,ValueError) else type(exc).__name__
            self.provider_error=f'Quét chưa hoàn tất: {detail}. Sẽ tự thử lại; chưa thể kết luận toàn thị trường.'
        finally:self.scanning=False
    async def loop(self):
        while True:
            await self.scan();await asyncio.sleep(60 if self.provider_error else 900)
    async def test(self,symbol,months=6):
        data=await self.provider.load(validate_symbol(symbol))
        b=backtest(data['bars'],months);b.update(symbol=symbol,source=data['source'],fetched_at=data['fetched_at'],cached=data['cached'])
        return b
