"""Local access by default; password-protected administration on a VPS."""
import base64
import binascii
import os
import secrets
from urllib.parse import urlsplit

from starlette.responses import JSONResponse


def settings():
    public = os.getenv('FINTECH_PUBLIC', '0') == '1'
    origin = os.getenv('PUBLIC_ORIGIN', '').rstrip('/')
    password = os.getenv('ADMIN_PASSWORD', '')
    if public:
        url = urlsplit(origin)
        if url.scheme != 'https' or not url.hostname or url.path or url.query or url.fragment or url.username:
            raise ValueError('PUBLIC_ORIGIN phải là địa chỉ HTTPS của máy chủ, không có đường dẫn.')
        if len(password) < 20:
            raise ValueError('ADMIN_PASSWORD cần tối thiểu 20 ký tự trước khi mở web ra Internet.')
    return public, origin, password


async def access_control(request, call_next):
    public, origin, password = settings()
    # Minimal liveness endpoint contains no account, market, or credential data.
    if request.url.path == '/healthz' and request.method == 'GET':
        return await call_next(request)
    host = request.headers.get('host', '').lower()
    allowed = {urlsplit(origin).netloc.lower()} if public else {'127.0.0.1:8010', 'localhost:8010', 'testserver'}
    if host not in allowed:
        return JSONResponse({'detail': 'Địa chỉ truy cập không hợp lệ.'}, status_code=403)
    if request.method not in ('GET', 'HEAD'):
        source = request.headers.get('origin')
        origins = {origin} if public else {'http://127.0.0.1:8010', 'http://localhost:8010'}
        if source and source not in origins:
            return JSONResponse({'detail': 'Nguồn yêu cầu không hợp lệ.'}, status_code=403)
    if public:
        user, supplied = '', ''
        try:
            scheme, encoded = request.headers.get('authorization', '').split(' ', 1)
            if scheme.lower() == 'basic':
                user, supplied = base64.b64decode(encoded, validate=True).decode('utf-8').split(':', 1)
        except (ValueError, UnicodeError, binascii.Error):
            pass
        user_ok = secrets.compare_digest(user.encode(), os.getenv('ADMIN_USERNAME', 'admin').encode())
        password_ok = secrets.compare_digest(supplied.encode(), password.encode())
        if not (user_ok and password_ok):
            return JSONResponse({'detail': 'Đăng nhập để quản trị Fintech Bot.'}, status_code=401,
                                headers={'WWW-Authenticate': 'Basic realm="Fintech Bot", charset="UTF-8"'})
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
