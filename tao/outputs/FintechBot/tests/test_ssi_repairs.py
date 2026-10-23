import asyncio
from types import SimpleNamespace
import pytest
from fintech.ssi_provider import SSI
from fintech.ssi_transport import SafeClient, SafeTransport, SafeConnection

def test_websocket_uses_trusted_ca_bundle(monkeypatch):
    import ssl
    import certifi
    from fintech import ssi_transport as module
    options=[]
    monkeypatch.setattr(module.websocket,'WebSocketApp',lambda *a,**k:
        SimpleNamespace(run_forever=lambda **kwargs:options.append(kwargs)))
    transport=SafeTransport('wss://example.test',skip_negotiation=True)
    transport.start()
    transport._thread.join(timeout=2)
    assert options[0]['sslopt']=={'ca_certs':certifi.where(),
        'cert_reqs':ssl.CERT_REQUIRED,'check_hostname':True}
    ssl.create_default_context(cafile=options[0]['sslopt']['ca_certs'])

def test_details_universe_filters_equities_and_handles_nested_pages(monkeypatch,tmp_path):
    from fintech import storage
    from ssi_fc_data.model import model
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init()
    p=object.__new__(SSI);p.config=None;p.model=model
    calls=[]
    def details(config,req):
        calls.append((req.market,req.pageIndex))
        rows=[{'Symbol':req.market+str(i),'SecType':'S'} for i in range(100)]
        rows.append({'Symbol':'WARRANT','SecType':'W'})
        return {'status':'Success','data':[{'RepeatedInfo':rows}]}
    p.client=SimpleNamespace(securities_details=details)
    result=asyncio.run(p.securities())
    assert len(result)==300 and 'WARRANT' not in result
    assert len(calls)==6
    assert storage.get('ssi_universe_v2')['symbols']==result


def test_ssi_dates_stay_distinct():
    p=object.__new__(SSI)
    base={'Open':10,'High':12,'Low':9,'Close':11,'Volume':100}
    assert p._row(dict(base,TradingDate='09/09/2026'))['date']=='2026-09-09'
    assert p._row(dict(base,TradingDate='2026-09-08'))['date']=='2026-09-08'
    with pytest.raises(ValueError):p._row(dict(base,TradingDate='invalid'))


def test_client_start_does_not_authenticate(monkeypatch):
    import requests
    def unexpected(*args,**kwargs):raise AssertionError('Network during startup')
    monkeypatch.setattr(requests,'post',unexpected)
    SafeClient(SimpleNamespace())


def test_negotiate_verifies_tls_and_never_prints_token(monkeypatch,capsys):
    import requests
    seen=[]
    def post(url,**kwargs):
        seen.append(kwargs)
        return SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'ConnectionToken':'opaque','ProtocolVersion':'1.5'})
    monkeypatch.setattr(requests,'post',post)
    t=SafeTransport('https://example.test/signalr',{'Authorization':'Bearer PRIVATE'})
    t._negotiate()
    assert seen[0]['verify'] is True
    assert seen[0]['timeout']==(10,25)
    assert 'PRIVATE' not in capsys.readouterr().out
    c=SafeConnection('https://example.test/signalr')
    c.close()


def test_scanner_recovers_after_universe_failure(monkeypatch,tmp_path):
    from fintech import storage
    from fintech.engine import Engine
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init()
    monkeypatch.delenv('SSI_CONSUMER_ID',raising=False)
    async def scenario():
        engine=Engine()
        await engine.provider.close()
        class Provider:
            calls=0
            async def universe(self):
                self.calls+=1
                if self.calls==1:raise ValueError('offline')
                return ['AAA','BBB']
        engine.provider=Provider()
        processed=[]
        async def analyze(symbol,force):processed.append(symbol)
        engine.analyze=analyze
        await engine.scan()
        assert not engine.scanning and engine.provider_error
        await engine.scan()
        assert processed==['AAA','BBB']
        assert engine.scan_done==2 and not engine.provider_error
    asyncio.run(scenario())
