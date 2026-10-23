"""Single Telegram long-poller; subscriptions and successful alert IDs persist."""
import asyncio
import json
import os
import re
import httpx
from . import storage
from .provider import now,validate_symbol
from .charts import ChartPhoto, create_chart
from .analysis_report import describe

TOKEN_FILE=storage.DATA/'telegram.json'

def saved_token():
    if TOKEN_FILE.exists():return json.loads(TOKEN_FILE.read_text()).get('token','')
    return os.getenv('TELEGRAM_BOT_TOKEN','')

HELP='''FINTECH BOT • BT1
/signals — tín hiệu phiên mới nhất
/stock MÃ_CỔ_PHIẾU — phân tích một mã
/fund MÃ_CỔ_PHIẾU — chỉ số cơ bản
/backtest MÃ_CỔ_PHIẾU — mô phỏng 6 tháng
/chart MÃ_CỔ_PHIẾU — ảnh chart và giá mới nhất
/subscribe — bật thông báo Buy/Sell
/unsubscribe — tắt thông báo
/share — lấy link mời bạn bè sử dụng bot
/status — trạng thái dữ liệu
/help — hướng dẫn
Tín hiệu TA dùng phiên đã đóng; giá gần nhất có thể trễ. Không tự động giao dịch.'''

class Telegram:
    def __init__(self,engine):
        self.engine=engine;self.token=saved_token();self.username=None;self.error=None;self.running=True
        self.client=httpx.AsyncClient(timeout=35)
    async def call(self,method,payload=None,token=None):
        token=token or self.token
        if not token:raise ValueError('Chưa kết nối Telegram.')
        try:
            r=await self.client.post(f'https://api.telegram.org/bot{token}/{method}',json=payload or {})
            d=r.json()
            if not d.get('ok'):raise ValueError(f"Telegram {d.get('error_code','')}: {d.get('description','Yêu cầu thất bại')}")
            return d['result']
        except (httpx.HTTPError,json.JSONDecodeError):raise ValueError('Không kết nối được Telegram; kiểm tra mạng.') from None
    async def connect(self,token):
        if not re.fullmatch(r'\d{5,}:[A-Za-z0-9_-]{20,}',token):raise ValueError('Token không đúng định dạng BotFather.')
        if self.token and token!=self.token:raise ValueError('Đã cấu hình bot. Dừng dịch vụ và xóa data/telegram.json để đổi bot an toàn.')
        me=await self.call('getMe',token=token)
        hook=await self.call('getWebhookInfo',token=token)
        if hook.get('url'):raise ValueError('Bot đang dùng webhook ở dịch vụ khác. Hãy tạo bot mới cho dự án này.')
        TOKEN_FILE.write_text(json.dumps({'token':token}));TOKEN_FILE.chmod(0o600)
        self.token=token;self.username=me['username'];self.error=None
        await self.register_commands()
        return {'username':self.username,'url':'https://t.me/'+self.username}
    async def register_commands(self):
        await self.call('setMyCommands',{'commands':[{'command':c,'description':d} for c,d in [('signals','Tín hiệu phiên mới nhất'),('stock','Phân tích mã: /stock MÃ_CỔ_PHIẾU'),('fund','Chỉ số cơ bản: /fund MÃ_CỔ_PHIẾU'),('backtest','Kiểm định: /backtest MÃ_CỔ_PHIẾU'),('chart','Ảnh chart: /chart MÃ_CỔ_PHIẾU'),('subscribe','Bật thông báo'),('unsubscribe','Tắt thông báo'),('share','Chia sẻ link bot'),('help','Hướng dẫn')]]})
    async def send_photo(self, chat, photo):
        if not self.token:raise ValueError('Chưa kết nối Telegram.')
        try:
            r=await self.client.post(f'https://api.telegram.org/bot{self.token}/sendPhoto',
                data={'chat_id':str(chat),'caption':photo.caption},
                files={'photo':(f'{photo.symbol}-chart.png',photo.png,'image/png')})
            result=r.json()
            if not result.get('ok'):
                raise ValueError(f"Telegram không gửi được ảnh ({result.get('error_code','?')}). Hãy thử lại.")
            return result['result']
        except (httpx.HTTPError,json.JSONDecodeError):
            raise ValueError('Không gửi được ảnh qua Telegram; kiểm tra mạng và thử lại.') from None
    async def send(self,chat,text):
        return await self.call('sendMessage',{'chat_id':chat,'text':text[:4000],
            'reply_markup':{'keyboard':[['/signals','/stock MÃ_CỔ_PHIẾU'],['/chart MÃ_CỔ_PHIẾU'],['/subscribe','/unsubscribe'],['/share','/help']],
                            'resize_keyboard':True,'is_persistent':True}})
    async def command(self,text,chat_id=None):
        parts=text.strip().split();cmd=(parts[0].split('@')[0].lower() if parts else '/help')
        if cmd=='/start':
            return 'Chào bạn! FINTECH BOT mở cho mọi người sử dụng.\nBấm /subscribe để nhận tín hiệu riêng; /unsubscribe để dừng bất kỳ lúc nào.\n\n'+HELP
        if cmd=='/help':return HELP
        if cmd=='/share':
            if not self.username:return 'Chưa có link: chủ bot cần kết nối token BotFather trước.'
            return f'Mời bạn dùng Fintech Bot: https://t.me/{self.username}?start=invite\nMở link → bấm Start → /subscribe để nhận tín hiệu. Không cần cung cấp token hay Chat ID.'
        if cmd in ('/subscribe','/unsubscribe'):
            if chat_id is None:return 'Lệnh này dùng trong Telegram sau khi kết nối bot.'
            storage.subscribe(chat_id,cmd=='/subscribe');return 'Đã bật thông báo TA Buy/Sell.' if cmd=='/subscribe' else 'Đã tắt thông báo.'
        if cmd=='/status':
            scope='danh sách thị trường SSI' if self.engine.universe_complete else 'chưa tải đủ danh sách SSI'
            warning=f"\n⚠ {self.engine.provider_error}" if self.engine.provider_error else ''
            return f"Nguồn {getattr(self.engine.provider,'source','SSI FastConnect Data')} • quét {scope} • chu kỳ 15 phút\nTiến độ: {self.engine.scan_done}/{self.engine.scan_total or len(self.engine.market_universe)} mã\nLần quét: {self.engine.last_scan or 'Đang khởi động'}\n{len(self.engine.signals)} mã có dữ liệu\nRealtime stream: {'Đang kết nối' if getattr(self.engine.provider,'_stream_started',False) else 'REST snapshot/cache'}\nTelegram: {'Đã cấu hình' if self.token else 'Chưa cấu hình'}"+warning
        if cmd=='/signals':
            ss=list(self.engine.signals.values());active=[s for s in ss if s['action']!='HOLD' and not s.get('cached') and not s.get('stale')]
            total=self.engine.scan_total or len(self.engine.market_universe) or len(ss)
            progress=f'{self.engine.scan_done}/{total} mã' if self.engine.scan_total else f'{total} mã'
            if active:
                active.sort(key=lambda s:(s['action'],s['symbol']))
                return '\n'.join([f'TÍN HIỆU SSI • {len(active)} mã BUY/SELL',f'Tiến độ: {progress} • '+('đang quét, kết quả tạm thời' if self.engine.scanning else 'xem /status để kiểm tra phạm vi'),
                    *[f"{s['symbol']} | {s['action']} | {s['close']:,.0f} đ | phiên {s['date']}" for s in active[:30]],
                    f'Hiển thị {min(30,len(active))}/{len(active)} mã. /stock MÃ_CỔ_PHIẾU để xem căn cứ và kế hoạch.',
                    'SELL dành cho vị thế đang giữ. Tín hiệu theo phiên ngày, không phải giá realtime.'])
            return '\n\n'.join(describe(s) for s in active[:20]) if active else f'Chưa có tín hiệu Buy/Sell trong dữ liệu hiện có. Đã xử lý {progress}. '+('Đã tải danh sách thị trường. ' if self.engine.universe_complete else 'Chưa tải đủ danh sách thị trường; kết quả chưa đầy đủ. ')+('Đang quét. ' if self.engine.scanning else '')+'Dùng /status xem nguồn và lỗi; /stock MÃ_CỔ_PHIẾU xem từng mã.'
        if cmd in ('/stock','/fund','/backtest','/chart'):
            if len(parts) != 2 or parts[1].upper() == 'MÃ_CỔ_PHIẾU':
                return f'Cú pháp: {cmd} MÃ_CỔ_PHIẾU\nThay MÃ_CỔ_PHIẾU bằng mã bạn muốn xem.'
            symbol=validate_symbol(parts[1])
            if cmd=='/chart':return await create_chart(self.engine,symbol)
            s=await self.engine.analyze(symbol)
            if cmd=='/stock':return describe(s)
            if cmd=='/fund':
                f=s['fundamentals'];fmt=lambda k: 'Chưa có' if f.get(k) is None else str(f[k])
                return f"{symbol} • {f.get('source',getattr(self.engine.provider,'source','SSI FastConnect Data'))}\nEPS {fmt('eps')} đ | P/E {fmt('pe')} | P/B {fmt('pb')}\nROE {fmt('roe')}% (kỳ {f.get('roe_period','—')})\nTăng DT {fmt('revenue_growth')}% | LN {fmt('profit_growth')}% (YoY, {f.get('period','—')})\nNợ/VCSH {fmt('debt_equity')}\nThu thập {f.get('fetched_at','—')}"
            b=await self.engine.test(symbol)
            return f"{symbol} • Backtest TA {b['start']} → {b['end']}\nLợi nhuận {b['return_pct']}% | Buy & hold {b['benchmark_pct']}%\nMax drawdown {b['max_drawdown_pct']}% | {b['trade_count']} giao dịch đã đóng\n{b['note']}"
        return 'Lệnh chưa hỗ trợ. Gõ /help để xem danh sách.'
    async def loop(self):
        while self.running:
            if not self.token:await asyncio.sleep(2);continue
            try:
                if not self.username:
                    me=await self.call('getMe')
                    await self.register_commands()
                    self.username=me['username']
                updates=await self.call('getUpdates',{'offset':storage.get('telegram_offset',0),'timeout':20,'allowed_updates':['message']})
                for u in updates:
                    m=u.get('message',{});chat=m.get('chat',{});cid=chat.get('id')
                    # Private conversations only: avoids group-wide accidental subscriptions.
                    if cid and chat.get('type')=='private':
                        storage.chat(cid,chat.get('first_name','Người dùng'))
                        try:reply=await self.command(m.get('text',''),cid)
                        except ValueError as e:reply=str(e)
                        except Exception:reply='Chưa xử lý được yêu cầu này. Hãy thử lại sau.'
                        if isinstance(reply,ChartPhoto):await self.send_photo(cid,reply)
                        else:await self.send(cid,reply)
                    storage.put('telegram_offset',u['update_id']+1)
                self.error=None
            except ValueError as e:self.error=str(e);await asyncio.sleep(5)
            except Exception:self.error='Lỗi xử lý cập nhật Telegram; đang thử lại.';await asyncio.sleep(5)
    async def alerts(self,signals):
        if not self.token:return
        for s in signals:
            if s['action']=='HOLD' or s['stale'] or s.get('cached'):continue
            for c in storage.chats():
                if not c['active']:continue
                key=f"{c['chat_id']}:{s['symbol']}:{s['date']}:{s['action']}:TA1"
                if storage.sent(key):continue
                try:await self.send(c['chat_id'],describe(s));storage.mark_sent(key)
                except ValueError as e:self.error=str(e)
                await asyncio.sleep(.1)
