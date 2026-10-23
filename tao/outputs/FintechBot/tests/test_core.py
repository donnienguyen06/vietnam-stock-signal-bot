import asyncio
import json
from datetime import date,timedelta
import numpy as np
import pytest
from fintech.strategy import indicators, signal, backtest
from fintech.provider import validate_symbol
from fintech.ssi_provider import SSI
from fintech.bot import Telegram
from fintech import storage

def bars(n=240):
    out=[]
    for i in range(n):
        c=30000+1500*np.sin(i/9)+i*8
        out.append(dict(date=(date(2025,1,1)+timedelta(days=i)).isoformat(),open=c-50,high=c+150,low=c-150,close=c,volume=1000000+i*1000))
    return out

def test_causal_indicators_do_not_change_with_future_prices():
    a=indicators(bars(150));b=indicators(bars(200))
    for col in ['ema20','ema50','rsi','support','resistance','rvol','buy','sell']:
        assert a[col].equals(b[col].iloc[:150])

def test_support_and_volume_exclude_today():
    a=bars(80); a[-1]['low']=1;a[-1]['volume']=9000000
    d=indicators(a)
    assert d.iloc[-1].support==min(x['low'] for x in a[-21:-1])
    assert d.iloc[-1].rvol==pytest.approx(9000000/np.mean([x['volume'] for x in a[-21:-1]]))

def test_flat_rsi_and_hold():
    a=bars(100)
    for x in a:x.update(open=100,high=100,low=100,close=100,volume=100)
    s=signal(a);assert s['rsi']==50;assert s['action']=='HOLD'

def test_monotonic_rsi():
    a=bars(100)
    for i,x in enumerate(a):x.update(open=100+i,high=100+i,low=100+i,close=100+i)
    assert signal(a)['rsi']==100

def test_missing_fundamentals_never_pass():
    s=signal(bars(),{'roe':20,'revenue_growth':30})
    assert s['value_status']=='MISSING';assert s['value_action']=='HOLD'

def test_sell_breakdown():
    a=bars();a[-1].update(open=10000,high=11000,low=9000,close=10000)
    assert signal(a)['action']=='SELL'

def test_insufficient_history():
    with pytest.raises(ValueError):signal(bars(30))
    with pytest.raises(ValueError):backtest(bars(60))

@pytest.mark.parametrize('s',['../secret','FPT;DROP','<script>','A','FPT VCB'])
def test_invalid_symbol(s):
    with pytest.raises(ValueError):validate_symbol(s)

def test_backtest_lots_and_costs():
    b=backtest(bars())
    assert b['max_drawdown_pct']<=0
    assert b['open_shares']%100==0
    for t in b['trades']:
        assert t['exit_date']>t['entry_date'];assert t['shares']%100==0
        assert t['pnl'] < t['shares']*(t['exit']-t['entry'])+100

def test_next_open_execution(monkeypatch):
    import fintech.strategy as st
    raw=bars(100);d=indicators(raw);d['buy']=False;d['sell']=False;d.loc[70,'buy']=True;d.loc[74,'sell']=True
    monkeypatch.setattr(st,'indicators',lambda x:d)
    b=st.backtest(raw)
    assert b['trade_count']==1
    t=b['trades'][0]
    assert t['entry_date']==raw[71]['date'];assert t['exit_date']==raw[75]['date']
    assert t['entry']==round(raw[71]['open']*1.001,2)

def test_persistence_and_subscription(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init()
    storage.chat(123,'Test');storage.subscribe(123,True)
    assert storage.chats()[0]['active']
    storage.mark_sent('unique');assert storage.sent('unique');assert not storage.sent('other')
    storage.put('telegram_offset',72);assert storage.get('telegram_offset')==72

def test_commands_and_unknown_input(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init()
    class E:signals={};last_scan=None
    async def run():
        b=Telegram(E())
        try:
            assert 'FINTECH BOT' in await b.command('/start')
            assert 'Cú pháp' in await b.command('/stock')
            assert 'chưa hỗ trợ' in await b.command('/unknown')
            assert 'Telegram' in await b.command('/subscribe')
        finally:await b.client.aclose()
    asyncio.run(run())

def test_cached_failure_is_explicit(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init()
    storage.put('market:ssi:FPT',dict(fetched_at='2020-01-01T00:00:00+07:00',bars=bars(),cached=False,error=None))
    async def run():
        c=SSI()
        async def fail(s):raise ValueError('offline')
        c.history=fail
        try:
            result=await c.load('FPT',True);assert result['cached'];assert 'SSI' in result['error']
        finally:await c.close()
    asyncio.run(run())

def test_alert_dedup_and_stale_suppression(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init();storage.chat(123,'Tester');storage.subscribe(123,True)
    async def run():
        b=Telegram(None);b.token='fake';sent=[]
        async def send(c,t):sent.append(c)
        b.send=send
        s=signal(bars());s.update(symbol='FPT',action='BUY',stale=False,cached=False,fetched_at='test')
        try:
            await b.alerts([s]);await b.alerts([s]);assert sent==[123]
            s.update(date='2099-01-01',stale=True);await b.alerts([s]);assert sent==[123]
        finally:await b.client.aclose()
    asyncio.run(run())
