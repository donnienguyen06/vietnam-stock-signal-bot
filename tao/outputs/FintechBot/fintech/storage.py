import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('FINTECH_DATA_DIR', ROOT/'data'))
DATA.mkdir(parents=True, exist_ok=True)

def connection():
    c=sqlite3.connect(DATA/'fintech.sqlite3',timeout=15)
    c.execute('PRAGMA journal_mode=WAL')
    return c

def init():
    with connection() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS subscribers(chat INTEGER PRIMARY KEY,name TEXT,active INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS alerts(key TEXT PRIMARY KEY,created TEXT DEFAULT CURRENT_TIMESTAMP);''')

def get(key, default=None):
    with connection() as c:r=c.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
    return json.loads(r[0]) if r else default

def put(key,value):
    with connection() as c:c.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',(key,json.dumps(value,ensure_ascii=False,allow_nan=False)))

def chat(chat_id,name):
    with connection() as c:c.execute('INSERT INTO subscribers(chat,name) VALUES (?,?) ON CONFLICT(chat) DO UPDATE SET name=excluded.name',(chat_id,name))

def subscribe(chat_id,enabled):
    with connection() as c:c.execute('UPDATE subscribers SET active=? WHERE chat=?',(int(enabled),chat_id))

def chats():
    with connection() as c:return [dict(chat_id=r[0],name=r[1],active=bool(r[2])) for r in c.execute('SELECT chat,name,active FROM subscribers')]

def sent(key):
    with connection() as c:return c.execute('SELECT 1 FROM alerts WHERE key=?',(key,)).fetchone() is not None

def mark_sent(key):
    with connection() as c:c.execute('INSERT OR IGNORE INTO alerts(key) VALUES (?)',(key,))

init()
