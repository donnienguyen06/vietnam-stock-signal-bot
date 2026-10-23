import pytest
from fastapi.testclient import TestClient
from fintech.app import app
from fintech.access import settings


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv('FINTECH_PUBLIC', '1')
    monkeypatch.setenv('PUBLIC_ORIGIN', 'https://bot.example.com')
    monkeypatch.setenv('ADMIN_USERNAME', 'owner')
    monkeypatch.setenv('ADMIN_PASSWORD', 'a-long-test-password-123456')
    return TestClient(app, base_url='https://bot.example.com')


def test_public_dashboard_and_account_data_require_login(server):
    for path in ['/', '/api/status', '/static/app.js']:
        response = server.get(path)
        assert response.status_code == 401
        assert 'Basic' in response.headers['www-authenticate']
    assert server.post('/api/telegram/connect', json={'token': 'x'*30}).status_code == 401


def test_valid_login_and_wrong_password(server):
    assert server.get('/api/status', auth=('owner', 'wrong')).status_code == 401
    response = server.get('/api/status', auth=('owner', 'a-long-test-password-123456'))
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'


def test_health_is_minimal_and_public(server):
    assert server.get('/healthz').json() == {'ok': True}


def test_public_cross_origin_write_rejected(server):
    response = server.post('/api/demo', json={'text': '/help'},
        auth=('owner', 'a-long-test-password-123456'), headers={'Origin': 'https://other.example'})
    assert response.status_code == 403
    response = server.post('/api/demo', json={'text': '/help'},
        auth=('owner', 'a-long-test-password-123456'), headers={'Origin': 'https://bot.example.com'})
    assert response.status_code == 200


def test_malformed_auth_and_host(server):
    assert server.get('/', headers={'Authorization': 'Basic ###'}).status_code == 401
    assert server.get('/', headers={'Host': 'evil.example'}).status_code == 403


def test_public_mode_fails_closed_without_password(server, monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD', '')
    with pytest.raises(ValueError, match='ADMIN_PASSWORD'):
        settings()


def test_public_requires_https(server, monkeypatch):
    monkeypatch.setenv('PUBLIC_ORIGIN', 'http://bot.example.com')
    with pytest.raises(ValueError, match='HTTPS'):
        settings()
