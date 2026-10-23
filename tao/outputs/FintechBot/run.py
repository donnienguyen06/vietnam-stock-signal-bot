#!/usr/bin/env python3
import os
import socket
import errno
from pathlib import Path
import uvicorn

def load_local_env():
    """Load the project's simple KEY=VALUE .env without an extra runtime dependency."""
    env_file = Path('.env')
    if not env_file.exists():
        return
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)

if __name__=='__main__':
    os.chdir(Path(__file__).resolve().parent)
    load_local_env()
    from fintech.access import settings
    public, _, _ = settings()
    host='0.0.0.0' if public else '127.0.0.1'
    listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    try:
        listener.bind((host,8010))
    except OSError as exc:
        listener.close()
        if exc.errno==errno.EADDRINUSE:
            raise SystemExit('Cổng 8010 đang có dịch vụ chạy. Dừng bản cũ bằng Ctrl+C ở terminal cũ trước khi chạy lại. Bản thứ hai chưa kết nối SSI/Telegram.')
        raise
    listener.listen(128)
    try:
        uvicorn.Server(uvicorn.Config('fintech.app:app',host=host,port=8010,workers=1,log_level='warning')).run(sockets=[listener])
    finally:
        listener.close()
