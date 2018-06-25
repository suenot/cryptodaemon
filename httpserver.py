#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from config import *
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json
from strategy import Strategy
from cryptobot import CryptoBot
from multiprocessing import Process


class ProcessManager:
    def __init__(self):
        self.workers = {}

    def add_worker(self, data):
        if self.request_is_valid(data) and self.find_worker(data['id']) is None:
            ss = 'strategy-settings'
            strategy_settings = data[ss] if ss in data else {}
            cb = CryptoBot(Strategy(data['api_keys']['exchange'], **strategy_settings), True)
            stream = Process(target=cb.start_trading)
            try:
                stream.start()
                self.workers[data['id']] = dict(process=stream, bot=cb)
                print(self.workers)
                return True
            except Exception as e:
                print(e)
                return False

    def get_alive_workers(self):
        return [x for x in self.workers]

    @staticmethod
    def request_is_valid(d):
        basic = 'action' in d and 'id' in d
        return basic

    def find_worker(self, uid):
        if uid in self.workers:
            return self.workers[uid]

    def kill_worker(self, uid):
        if self.find_worker(uid):
            try:
                self.workers[uid]['bot'].stop_trading()
                self.workers[uid]['process'].terminate()
                if uid in self.workers:
                    del self.workers[uid]
                return True
            except Exception as e:
                print(e)
                return False


class PostHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super(BaseHTTPRequestHandler, self).__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode(ENCODING))
        self.server.process_query(data)

    def respond(self, code, answer):
        self.send_response(code)
        self.end_headers()
        response = BytesIO()
        response.write(bytes(answer, ENCODING))
        self.wfile.write(response.getvalue())


class Server(HTTPServer):
    def __init__(self, *args, **kwargs):
        self.pm = ProcessManager()
        super(HTTPServer, self).__init__(*args, **kwargs)

    @staticmethod
    def keys_structured(api_key, secret_key):
        return dict(apiKey=api_key, secret=secret_key, enableRateLimit=True)

    def process_query(self, data):
        if ACTION in data:
            # set exchange by name + api key
            act = data[ACTION]
            if act == 'start':
                if AKEY in data:
                    api = data[AKEY]
                    if EXCHANGE in api and PKEY in api and SKEY in api:
                        ex = SUPPORTED_EXCHANGES[api[EXCHANGE]]
                        if ex is None:
                            self.respond(WRONG_DATA, 'Non supported exchange!')
                            return False
                        else:
                            api[EXCHANGE] = ex(self.keys_structured(api[PKEY], api[SKEY]))
                    else:
                        self.respond(WRONG_DATA, 'Exchange or API-key unfilled!')
                        return False
                else:
                    self.respond(WRONG_DATA, 'Not see key {} in your data!'.format(AKEY))
                    return False

                started = self.pm.add_worker(data)
                print(self.pm.workers)
                if started is None:
                    self.RequestHandlerClass.respond(WRONG_DATA, 'CryptoDaemon already started')
                elif started:
                    self.RequestHandlerClass.respond(SUCCESS, 'CryptoDaemon started successfully')
                else:
                    self.respond(SERVER_ERROR, 'ERR: Shit happened. ')
            elif act == 'stop':
                if self.pm.kill_worker(data['id']):
                    self.respond(SUCCESS, 'CryptoDaemon instance stopped')
                else:
                    self.respond(SERVER_ERROR, 'ERR: Can not find your worker process by id..,')
            elif act == 'get-alive-workers':
                self.respond(SUCCESS, str(self.pm.get_alive_workers()))
            else:
                self.respond(WRONG_DATA, 'Unknown action!')


if __name__ == '__main__':
    httpd = Server((DEFAULT_HOST, API_PORT), PostHandler)
    httpd.serve_forever()
