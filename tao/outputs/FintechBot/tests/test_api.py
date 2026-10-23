from fastapi.testclient import TestClient
from fintech.app import app
client=TestClient(app)
def test_local_status_and_page():
    assert client.get('/').status_code==200
    assert client.get('/api/status').json()['interval']==900

def test_cross_origin_mutation_rejected():
    assert client.post('/api/scan',headers={'Origin':'https://evil.example'}).status_code==403

def test_rebinding_rejected():
    assert client.get('/api/status',headers={'Host':'evil.example'}).status_code==403

def test_input_validation_and_no_token_leak():
    assert client.post('/api/telegram/connect',json={'token':'bad'}).status_code==422
    assert 'token' not in client.get('/api/status').text
    assert client.get('/api/backtest/FPT?months=12').status_code==400

def test_unknown_command_is_safe():
    r=client.post('/api/demo',json={'text':'/doesnotexist'})
    assert r.status_code==200
    assert 'chưa hỗ trợ' in r.json()['reply']
