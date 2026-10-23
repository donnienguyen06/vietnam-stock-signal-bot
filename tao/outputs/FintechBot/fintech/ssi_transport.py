"""Compatibility layer for SSI SDK 2.2.2: verified TLS, timeouts, no token prints."""
import threading
import time
import ssl
import certifi
import websocket
from dataclasses import asdict
from urllib.parse import urlencode
import requests
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.signalr import Connection
from ssi_fc_data.signalr.transports._transport import WebsocketTransport
from ssi_fc_data.signalr.transports.connection import ConnectionState


class SafeClient(MarketDataClient):
    def __init__(self, config):
        # Defer authentication until a worker makes the first request.
        self._config=config
        self._header={'Content-Type':'application/json','Accept':'application/json'}
        self._token=None
        self._expires=0
        self._auth_lock=threading.Lock()

    def _get_access_token(self):
        with self._auth_lock:
            if not self._config.consumerID or not self._config.consumerSecret:
                raise ValueError('Chưa điền SSI_CONSUMER_ID và SSI_CONSUMER_SECRET trong .env.')
            if self._token and time.monotonic()<self._expires:return self._token
            response=requests.post(self._config.url+'api/v2/Market/AccessToken',
                json={'consumerID':self._config.consumerID,'consumerSecret':self._config.consumerSecret},
                timeout=(10,25),verify=True)
            response.raise_for_status()
            result=response.json()
            data=result.get('data') or {}
            token=data.get('accessToken')
            if result.get('status')!=200 or not token:
                raise ValueError('SSI từ chối xác thực. Kiểm tra Consumer ID/Secret và quyền FC Data.')
            self._token=token
            self._expires=time.monotonic()+300
            return token

    def _make_get_request(self, url, req):
        for attempt in range(2):
            response=requests.get(self._config.url+url,params=asdict(req),
                headers={**self._header,'Authorization':'Bearer '+self._get_access_token()},
                timeout=(10,25),verify=True)
            if response.status_code==401 and attempt==0:
                self._expires=0
                continue
            response.raise_for_status()
            return response.json()


class SafeTransport(WebsocketTransport):
    def __init__(self,*args,**kwargs):
        kwargs['verify_ssl']=True
        super().__init__(*args,**kwargs)

    def start(self, connectionData=''):
        self.conn_data=connectionData
        if self.state==ConnectionState.connected:return False
        if not self.skip_negotiation:self._negotiate()
        self.state=ConnectionState.connecting
        self._ws=websocket.WebSocketApp(self.url,header=self.headers,
            on_message=self.on_message,on_error=self.on_socket_error,
            on_close=self.on_close,on_open=self.on_open)
        # The SDK passes an empty sslopt when verification is enabled. On
        # python.org macOS builds that can leave OpenSSL without trusted CAs.
        self._thread=threading.Thread(target=lambda:self._ws.run_forever(
            sslopt={'ca_certs':certifi.where(),'cert_reqs':ssl.CERT_REQUIRED,
                    'check_hostname':True}),daemon=True)
        self._thread.start()
        return True

    def _negotiate(self):
        query=urlencode({'connectionData':self.conn_data,'clientProtocol':self.protocol_version})
        response=requests.post(self._format_url(self.url,'negotiate',query),
            headers=self.headers,verify=True,timeout=(10,25))
        response.raise_for_status()
        self.url=self._get_socket_url(response.json())


class SafeConnection(Connection):
    def __init__(self,url,headers=None,**kwargs):
        super().__init__(url,headers,verify_ssl=True,**kwargs)
        self._Connection__transport=SafeTransport(url,headers,on_message=self._on_message,**kwargs)

    def close(self):
        transport=self._Connection__transport
        transport.connection_checker.stop()
        if transport._ws:transport._ws.close()
