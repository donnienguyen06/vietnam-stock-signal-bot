from fintech.analysis_report import analysis,describe

def sample(action='BUY',**kwargs):
    return dict(symbol='AAA',action=action,close=100,ema20=98,ema50=95,rsi=60,rvol=1.4,
        atr=3,support=90,resistance=105,date='2026-09-10',fetched_at='test',reasons=['Cross'],**kwargs)

def test_price_order_and_rr():
    p=analysis(sample())['plan']
    assert 0<p['stop']<p['entry_low']<=p['entry_high']<p['target1']<p['target2']
    assert (p['target1']-p['entry_high'])/(p['entry_high']-p['stop'])==2
    assert p['resistance_in_path']

def test_no_buy_plan_for_sell_hold_or_stale():
    for s in [sample('SELL'),sample('HOLD'),sample(cached=True),sample(stale=True)]:
        assert analysis(s)['plan'] is None
    assert 'bán khống' in describe(sample('SELL'))
    assert 'không phải dự báo' in describe(sample())
    assert len(describe(sample()))<4000
