"""SSI FastConnect Data adapter based on the SDK supplied with the project.

The SDK refreshes the Bearer access token internally. This adapter deliberately
supports market data only: it never calls a trading endpoint.
"""
import asyncio
import importlib
import json
import os
from datetime import datetime, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

from . import storage
from .provider import SYMBOLS, number, validate_symbol

TZ = ZoneInfo('Asia/Ho_Chi_Minh')


def configured():
    return bool(os.getenv('SSI_CONSUMER_ID','').strip() and os.getenv('SSI_CONSUMER_SECRET','').strip())


class SSI:
    source = 'SSI FastConnect Data'
    def __init__(self):
        try:
            self.client_module = importlib.import_module('ssi_fc_data.fc_md_client')
            self.model = importlib.import_module('ssi_fc_data.model.model')
            self.config = type('SSIConfig', (), {
                'auth_type':'Bearer',
                'consumerID':os.getenv('SSI_CONSUMER_ID',''),
                'consumerSecret':os.getenv('SSI_CONSUMER_SECRET',''),
                'url':os.getenv('SSI_BASE_URL','https://fc-data.ssi.com.vn/').rstrip('/')+'/',
                'stream_url':os.getenv('SSI_STREAM_URL','https://fc-datahub.ssi.com.vn/').rstrip('/')+'/'
            })()
            from .ssi_transport import SafeClient
            self.client = SafeClient(self.config)
        except (ImportError,AttributeError,TypeError) as e:
            raise ValueError('Chưa cài SDK SSI FastConnect Data hoặc cấu hình SDK không đúng.') from e
        self._quotes={};self._lock=Lock();self._stream_started=False

    async def close(self):
        stream=getattr(self,'stream',None)
        connection=getattr(stream,'connection',None)
        if connection:
            try:connection.close()
            except Exception:pass

    def _request(self, fn, req):
        result=fn(self.config,req)
        if isinstance(result,dict) and result.get('status')=='NoDataFound':return []
        if not isinstance(result,dict) or result.get('status') not in (None,200,'Success'):
            raise ValueError('SSI từ chối yêu cầu dữ liệu; kiểm tra quyền API hoặc thử lại sau.')
        return result.get('data', result.get('Data', result))

    @staticmethod
    def _rows(data):
        if isinstance(data,list):
            nested=[]
            for item in data:
                if isinstance(item,dict) and ('RepeatedInfo' in item or 'repeatedInfo' in item):
                    nested.extend(SSI._rows(item))
                else:nested.append(item)
            return nested
        if isinstance(data,dict):
            for key in ('data','Data','items','Items','values','Value','result','Result','RepeatedInfo','repeatedInfo'):
                value=data.get(key)
                if isinstance(value,list):return SSI._rows(value)
                nested=SSI._rows(value)
                if nested:return nested
        return []

    @staticmethod
    def _field(row,*names):
        if not isinstance(row,dict):return None
        low={str(k).lower():v for k,v in row.items()}
        for name in names:
            if name.lower() in low:return low[name.lower()]
        return None

    def _row(self,row):
        date_value=self._field(row,'tradingDate','TradingDate','date','Date','tradingTime')
        if isinstance(date_value,str):
            raw=date_value[:10]
            for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y'):
                try:
                    date_value=datetime.strptime(raw,fmt).date().isoformat()
                    break
                except ValueError:continue
            else:raise ValueError('SSI trả ngày giao dịch không hợp lệ.')
        else:raise ValueError('SSI thiếu ngày giao dịch.')
        values={k:number(self._field(row,*names)) for k,names in {
            'open':('openPrice','OpenPrice','open'), 'high':('highPrice','HighestPrice','high'),
            'low':('lowPrice','LowestPrice','low'), 'close':('closePrice','ClosePrice','lastPrice','last','close'),
            'volume':('volume','Volume','totalVolume','TotalMatchVolume')}.items()}
        if any(values[k] is None for k in ('open','high','low','close','volume')):raise ValueError('SSI trả OHLCV thiếu trường bắt buộc.')
        return dict(date=date_value,**values,raw_close=values['close'])

    async def securities(self):
        symbols=[]
        # The SDK accepts board filters; querying all three keeps this working
        # across SSI deployments where Market=ALL is not enabled.
        for market in ('HOSE','HNX','UPCOM'):
            seen=set()
            for page in range(1,101):
                page_size=100
                data=await asyncio.to_thread(self._request,self.client.securities_details,self.model.securities_details(market,'',page,page_size))
                rows=self._rows(data)
                page_symbols={str(self._field(r,'symbol') or '') for r in rows}
                if page_symbols and page_symbols<=seen:break
                seen.update(page_symbols)
                for row in rows:
                    if self._field(row,'SecType')!='S':continue
                    s=self._field(row,'symbol','Symbol','stockSymbol','StockSymbol')
                    if s:
                        s=str(s).strip().upper()
                        if s and s not in symbols:symbols.append(s)
                # SSI may return an entire board in a single RepeatedInfo envelope.
                envelopes=data if isinstance(data,list) else [data]
                totals=[number(self._field(item,'TotalNoSym')) for item in envelopes if isinstance(item,dict)]
                expected=max((n for n in totals if n is not None),default=0)
                if expected and len(seen)>=expected:break
                if len(rows)<page_size:break
        if len(symbols)<50:raise ValueError(f'SSI chỉ trả {len(symbols)} mã từ ba sàn; chưa đủ xác nhận toàn thị trường.')
        storage.put('ssi_universe_v2',{'symbols':symbols,'date':datetime.now(TZ).date().isoformat()});return symbols

    async def universe(self):
        cached=storage.get('ssi_universe_v2')
        if cached and cached.get('date')==datetime.now(TZ).date().isoformat():return cached['symbols']
        return await self.securities()

    async def history(self,symbol):
        symbol=validate_symbol(symbol);today=datetime.now(TZ);start=today-timedelta(days=450)
        rows=[]
        for page in range(1,11):
            req=self.model.daily_ohlc(symbol,start.strftime('%d/%m/%Y'),today.strftime('%d/%m/%Y'),page,100,True)
            data=await asyncio.to_thread(self._request,self.client.daily_ohlc,req)
            batch=self._rows(data)
            rows.extend(self._row(r) for r in batch)
            if len(batch)<100:break
        rows=sorted({r['date']:r for r in rows}.values(),key=lambda x:x['date'])
        if (today.hour,today.minute)<(15,0):
            rows=[r for r in rows if r['date']<today.date().isoformat()]
        if len(rows)<60:raise ValueError(f'SSI chỉ trả {len(rows)} phiên; cần ít nhất 60.')
        return rows

    async def quote(self,symbol):
        symbol=validate_symbol(symbol)
        # SSI's streaming callback updates this cache. REST intraday gives a safe
        # fresh snapshot when the stream has not delivered the symbol yet.
        with self._lock:q=self._quotes.get(symbol)
        if q and (datetime.now(TZ)-datetime.fromisoformat(q['timestamp'])).total_seconds()<120:return q
        today=datetime.now(TZ)
        req=self.model.intraday_ohlc(symbol,today.strftime('%d/%m/%Y'),today.strftime('%d/%m/%Y'),1,100,False,1)
        data=await asyncio.to_thread(self._request,self.client.intraday_ohlc,req)
        rows=self._rows(data)
        if not rows:raise ValueError('SSI chưa trả giá trong ngày cho mã này.')
        row=rows[0];price=number(self._field(row,'lastPrice','LastPrice','closePrice','ClosePrice','price','Price'))
        if price is None:price=number(self._field(row,'close','Close'))
        if not price or price<=0:raise ValueError('SSI trả giá realtime không hợp lệ.')
        return dict(price=price,reference=number(self._field(row,'referencePrice','RefPrice','refPrice')),
            volume=number(self._field(row,'volume','Volume','totalVolume')),timestamp=str(self._field(row,'tradingDate','date') or '')+' '+str(self._field(row,'time','tradingTime') or ''),source='SSI FastConnect • snapshot intraday')

    async def fundamentals(self,symbol):
        return dict(source='SSI FastConnect',fetched_at=datetime.now(TZ).isoformat(),errors=['Chưa tích hợp nguồn BCTC SSI; bộ lọc cơ bản không đánh giá khi thiếu dữ liệu.'],roe=None,revenue_growth=None,profit_growth=None,debt_equity=None)

    def _on_stream(self,message):
        if isinstance(message,list):
            for item in message:self._on_stream(item)
            return
        if isinstance(message,str):
            try:message=json.loads(message)
            except json.JSONDecodeError:return
        content=message.get('Content') if isinstance(message,dict) else None
        if isinstance(content,list):
            for item in content:self._on_stream(item)
            return
        if isinstance(content,str):
            try:content=json.loads(content)
            except json.JSONDecodeError:return
        if not isinstance(content,dict):content=message
        symbol=self._field(content,'symbol','stockSymbol','ticker')
        price=number(self._field(content,'lastPrice','last','matchPrice','closePrice'))
        if not symbol or not price or price<=0:return
        with self._lock:self._quotes[str(symbol).upper().strip()]=dict(price=price,reference=number(self._field(content,'refPrice','referencePrice','reference')),volume=number(self._field(content,'totalMatchVolume','totalVolume','volume')),timestamp=datetime.now(TZ).isoformat(),source='SSI FastConnect • streaming X:ALL')

    async def start_stream(self):
        from .ssi_transport import SafeConnection
        api=importlib.import_module('ssi_fc_data.model.api')
        while True:
            try:
                token=await asyncio.to_thread(self.client._get_access_token)
                self.stream=type('Stream',(),{})()
                connection=SafeConnection(self.config.stream_url+api.SIGNALR,
                    {'Authorization':'Bearer '+token},on_close=lambda:setattr(self,'_stream_started',False))
                self.stream.connection=connection
                hub=connection.register_hub(api.SIGNALR_HUB_MD)
                hub.client.on(api.SIGNALR_METHOD,self._on_stream)
                def opened():
                    hub.server.invoke('SwitchChannels','X:ALL')
                    self._stream_started=True
                connection.on_open_callback(opened)
                await asyncio.to_thread(connection.start)
                await asyncio.sleep(10)
                while self._stream_started:await asyncio.sleep(5)
            except asyncio.CancelledError:raise
            except Exception:
                self._stream_started=False
            finally:
                await self.close()
            await asyncio.sleep(15)

    async def load(self,symbol,force=False):
        cached=storage.get('market:ssi:'+symbol)
        if cached and not force and (datetime.now(TZ)-datetime.fromisoformat(cached['fetched_at'])).total_seconds()<300:return cached
        try:bars=await self.history(symbol)
        except Exception:
            if cached:
                return dict(cached,cached=True,error='SSI tạm thời không khả dụng; đang dùng lịch sử lưu trước đó.')
            raise ValueError('Chưa tải được lịch sử SSI; hãy thử lại sau.') from None
        try:quote=await self.quote(symbol)
        except Exception:quote=None
        result=dict(symbol=symbol,bars=bars,fundamentals=await self.fundamentals(symbol),quote=quote,fetched_at=datetime.now(TZ).isoformat(),source=self.source,cached=False,error=None)
        storage.put('market:ssi:'+symbol,result);return result
