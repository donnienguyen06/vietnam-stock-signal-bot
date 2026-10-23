"""Causal indicators: all rolling thresholds exclude the decision bar."""
import math
import pandas as pd


def indicators(bars):
    d = pd.DataFrame(bars).copy().sort_values('date').reset_index(drop=True)
    c = d.close
    d['ema20'] = c.ewm(span=20, adjust=False).mean()
    d['ema50'] = c.ewm(span=50, adjust=False).mean()
    delta = c.diff()
    # Wilder RSI: arithmetic seed over 14 changes, then Wilder recursion.
    gains, losses = delta.clip(lower=0), -delta.clip(upper=0)
    rsi = [float('nan')] * len(d)
    if len(d) > 14:
        g, l = gains.iloc[1:15].mean(), losses.iloc[1:15].mean()
        for i in range(14, len(d)):
            if i > 14:
                g, l = (g * 13 + gains.iloc[i]) / 14, (l * 13 + losses.iloc[i]) / 14
            rsi[i] = 50 if g == l == 0 else (100 if l == 0 else 100 - 100 / (1 + g / l))
    d['rsi'] = rsi
    d['support'] = d.low.shift(1).rolling(20).min()
    d['resistance'] = d.high.shift(1).rolling(20).max()
    d['rvol'] = d.volume / d.volume.shift(1).rolling(20).mean().replace(0, float('nan'))
    tr = pd.concat([d.high-d.low, (d.high-c.shift()).abs(), (d.low-c.shift()).abs()], axis=1).max(axis=1)
    d['atr'] = tr.ewm(alpha=1/14, adjust=False).mean()
    d['buy'] = (d.ema20.shift() <= d.ema50.shift()) & (d.ema20 > d.ema50) & (d.rsi > 50) & (d.rsi < 70) & (d.rvol >= 1)
    d['sell'] = (c < d.support) | ((d.rsi.shift() > 70) & (d.rsi < d.rsi.shift())) | ((d.ema20.shift() >= d.ema50.shift()) & (d.ema20 < d.ema50))
    d.loc[:58, ['buy', 'sell']] = False
    return d


def signal(bars, fundamentals=None):
    if len(bars) < 60:
        raise ValueError('Cần ít nhất 60 phiên để tính tín hiệu.')
    d = indicators(bars)
    a, p = d.iloc[-1], d.iloc[-2]
    reasons = []
    if a.close < a.support: reasons.append('Giá đóng cửa thủng đáy 20 phiên trước')
    if p.rsi > 70 and a.rsi < p.rsi: reasons.append('RSI quay đầu sau vùng quá mua')
    if p.ema20 >= p.ema50 and a.ema20 < a.ema50: reasons.append('EMA20 cắt xuống EMA50')
    action = 'SELL' if a.sell else 'BUY' if a.buy else 'HOLD'
    if action == 'BUY': reasons = ['EMA20 cắt lên EMA50', '50 < RSI14 < 70', 'Khối lượng ≥ trung bình 20 phiên trước']
    if action == 'HOLD': reasons = ['Chưa hội đủ điều kiện mua hoặc bán mới']
    f = fundamentals or {}
    keys = ['roe', 'revenue_growth', 'profit_growth']
    complete = all(f.get(k) is not None for k in keys)
    value_pass = complete and all(f[k] > 15 for k in keys)
    momentum = bool(value_pass and a.rvol >= 1.5 and a.close > a.resistance and a.ema20 > a.ema50)
    return dict(action=action, date=str(a.date), close=round(a.close, 2), change_pct=round((a.close/p.close-1)*100,2),
        ema20=round(a.ema20,2), ema50=round(a.ema50,2), rsi=round(a.rsi,2), rvol=round(a.rvol,2),
        support=round(a.support,2), resistance=round(a.resistance,2), atr=round(a.atr,2),
        stop_reference=round(max(0,a.close-2*a.atr),2), reasons=reasons,
        value_status='PASS' if value_pass else 'FAIL' if complete else 'MISSING',
        value_action='BUY' if momentum and not a.sell else 'HOLD',
        volume=int(a.volume), series=[dict(date=str(x.date), close=round(x.close,2), ema20=round(x.ema20,2), ema50=round(x.ema50,2)) for x in d.tail(100).itertuples()])


def backtest(bars, months=6, fee=.0015, sell_tax=.001, slippage=.001):
    """Long-only, next-open execution, 100-share lots, conservative 3-session lock.
    Price series is adjusted by source ratio; volume remains raw. Educational simulation.
    """
    d = indicators(bars)
    if len(d) < 80: raise ValueError('Cần tối thiểu 80 phiên cho backtest có warm-up.')
    cutoff = pd.Timestamp(d.iloc[-1].date) - pd.DateOffset(months=months)
    start = max(60, next((i for i, x in enumerate(d.date) if pd.Timestamp(x) >= cutoff), len(d)-1))
    if len(d)-start < 20: raise ValueError('Chưa đủ dữ liệu sau warm-up.')
    initial = cash = 100_000_000.0
    shares = 0; entry = None; trades = []; equity = []; lock_until = -1
    for i in range(start,len(d)):
        a, prev = d.iloc[i],d.iloc[i-1]
        if shares and prev.sell and i >= lock_until:
            px = a.open*(1-slippage); proceeds=shares*px*(1-fee-sell_tax)
            cash += proceeds
            trades.append(dict(entry_date=entry['date'], exit_date=str(a.date), entry=entry['price'], exit=round(px,2), shares=shares, pnl=round(proceeds-entry['cost'],2)))
            shares=0;entry=None
        elif not shares and prev.buy:
            px=a.open*(1+slippage); shares=int(cash/(px*(1+fee))//100)*100
            if shares:
                cost=shares*px*(1+fee); cash-=cost;entry=dict(date=str(a.date),price=round(px,2),cost=cost);lock_until=i+3
        equity.append(dict(date=str(a.date), equity=round(cash+shares*a.close,2)))
    values=pd.Series([x['equity'] for x in equity]);peak=values.cummax().clip(lower=initial)
    return dict(start=equity[0]['date'],end=equity[-1]['date'],sessions=len(equity),warmup_sessions=start,
        initial=initial,final=equity[-1]['equity'],return_pct=round((values.iloc[-1]/initial-1)*100,2),
        max_drawdown_pct=round(((values/peak)-1).min()*100,2), trades=trades,trade_count=len(trades),
        win_rate=round(sum(t['pnl']>0 for t in trades)/len(trades)*100,2) if trades else None,
        benchmark_pct=round((d.iloc[-1].close/d.iloc[start].open-1)*100,2),open_shares=shares,
        equity=equity, costs=dict(fee_each_side=fee,sell_tax=sell_tax,slippage_each_side=slippage),
        note='TA בלבד' if False else 'TA; khớp giá mở cửa phiên sau; lô 100; khóa bán 3 phiên; vị thế cuối kỳ định giá đóng cửa. Chưa mô phỏng trần/sàn, cổ tức tiền, thanh khoản và lịch nghỉ thanh toán đầy đủ.')
