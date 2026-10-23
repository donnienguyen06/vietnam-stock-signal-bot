from fintech.engine import Engine
from fintech.ssi_provider import SSI
from fintech import storage

def test_missing_keys_never_selects_other_source(monkeypatch):
    monkeypatch.delenv('SSI_CONSUMER_ID',raising=False)
    monkeypatch.delenv('SSI_CONSUMER_SECRET',raising=False)
    engine=Engine()
    assert isinstance(engine.provider,SSI)
    assert engine.provider_error

def test_legacy_watchlist_is_not_universe(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DATA',tmp_path);storage.init()
    storage.put('watchlist',['AAA','BBB'])
    assert Engine().watchlist==[]
