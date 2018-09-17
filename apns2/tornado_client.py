#!/usr/bin/env python
# -*- coding: utf-8 -*-

from builtins import range
from builtins import object
from json import dumps
import time
import itertools
import logging
import pprint
import random
from functools import partial

from tornado.ioloop import PeriodicCallback
from http2 import SimpleAsyncHTTP2Client
import jwt

log = logging.getLogger('apns2.tornado_client')

NOTIFICATION_PRIORITY = dict(immediate='10', delayed='5')


class APNsClient(object):

    def __init__(self, key_file=None, teams_data=None, server=None, port=None, max_connections=3, conn_config=None):
        self._header_format = 'bearer %s'
        self.__url_pattern = '/3/device/{token}'

        if server:
            self.server = server
        else:
            self.server = None
        self.port = port or 443

        self._jwt_expire_interval = 3000  # 50 minuts
        self._teams = {}
        self.max_connections = max_connections

        self.configure(key_file, teams_data)
        self.conn_config = conn_config

    def configure(self, key_file, teams_data):
        """ Настройка ID команд APNS
        Args:
            teams_data: dict
        """
        for team_name, data in teams_data.items():
            if not data.get('NAME'):
                data['NAME'] = team_name

            if not data.get('conns'):
                data['conns'] = {}

            with open(key_file.format(key_id=data['KEY_ID']), 'r') as tmp:
                data['auth_key'] = tmp.read()

            if data.get('DEFAULT'):
                self._teams['default'] = data
            elif data.get('BUNDLES'):
                for app_bundle_id in data.get('BUNDLES'):
                    self._teams[app_bundle_id] = data
            else:
                raise Exception('Team %s is not default and has no bundles: %s', team_name, data)

    def get_conn(self, app_bundle_id, sandbox):
        team = self._get_team(app_bundle_id)
        pool = team['conns'].setdefault(sandbox,[])
        if not len(pool):
            for i in range(self.max_connections):
                client_name = "{}_{}_{}".format(team['NAME'], sandbox, i)
                pool.append(self._init_client(sandbox, client_name))

        return random.choice(pool)

    def _init_client(self, sandbox, client_name):
        if self.server:
            server = self.server
        else:
            server = 'api.development.push.apple.com' if sandbox else 'api.push.apple.com'
        return SimpleAsyncHTTP2Client(
            host=server,
            port=self.port,
            secure=True,
            enable_push=True,
            connect_timeout=20,
            request_timeout=20,
            max_streams=1000,
            http_client_key=client_name,
            conn_config=self.conn_config
        )

    def _get_team(self, topic):
        return self._teams.get(topic, self._teams.get('default'))

    def _get_jwt(self, topic):
        team = self._get_team(topic)

        token = team.get('jwt')

        if token:
            return token
        else:
            return self._generate_jwt(team)

    def _generate_jwt(self, team):
        now = int(time.time())
        claim = dict(
            iss=team['TEAM_ID'],
            iat=now
        )
        headers = dict(kid=team['KEY_ID'])

        token = jwt.encode(claim, team['auth_key'], algorithm='ES256', headers=headers).decode('ascii')
        team['jwt'] = token

        if not team.get('jwt_regenerator'):
            func = partial(self._generate_jwt, team)
            team['jwt_regenerator'] = PeriodicCallback(func, self._jwt_expire_interval * 1000)

        if not team['jwt_regenerator'].is_running():
            team['jwt_regenerator'].start()

        return token

    def prepare_payload(self, notification):
        return dumps(notification.dict(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    def prepare_headers(self, priority, topic, expiration, collapse_id=None):
        headers = {
            'apns-priority': priority
        }

        if topic:
            headers['apns-topic'] = topic

        if expiration is not None:
            headers['apns-expiration'] = "%d" % expiration

        auth_token = self._get_jwt(topic)

        headers['authorization'] = self._header_format % auth_token

        if collapse_id:
            headers['apns-collapse-id'] = collapse_id

        return headers

    def send_push(self, token, topic, notification, sandbox=False, priority=NOTIFICATION_PRIORITY['immediate'], expiration=None, cb=None):
        url = self.__url_pattern.format(token=token)
        json_payload = self.prepare_payload(notification)
        headers = self.prepare_headers(priority, topic, expiration)

        return self.get_conn(topic, sandbox).fetch(url, method='POST', body=json_payload, headers=headers, callback=cb, raise_error=False)
