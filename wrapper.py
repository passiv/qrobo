#!/usr/bin/env python

import sys
import json
from collections import namedtuple
import requests
import datetime
import shelve
import argparse
import logging

logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] %(levelname)s - %(message)s - {%(filename)s:%(lineno)d}',
    stream=sys.stdout,
)


class QuestradeBaseException(Exception):
    pass


class QuestradeAuthException(QuestradeBaseException):
    pass


class QuestradeCannotFindRefreshTokenException(QuestradeBaseException):
    pass


class QuestradeRequestException(QuestradeBaseException):
    pass


class QuestradeSymbolNoExactMatchFound(QuestradeBaseException):
    pass


class RefreshToken(object):
    database_name = '/tmp/refresh.db'

    def __init__(self, token):
        self.token = token

    def __str__(self):
        return self.token

    def __repr__(self):
        return '<RefreshToken %s>' % self.token

    @classmethod
    def load(cls):
        try:
            db = shelve.open(cls.database_name)
            refresh_token = db['refresh_token']
            db.close()
            return cls(refresh_token)
        except:
            raise QuestradeCannotFindRefreshTokenException

    @classmethod
    def dump(cls, refresh_token):
        db = shelve.open(cls.database_name)
        db['refresh_token'] = str(refresh_token)
        db.close()


class AccessToken(object):
    def __init__(self, api_server, token, token_type, refresh_token, expires=1800):
        self.api_server = api_server
        self.token = token
        self.type = token_type
        self.refresh_token = RefreshToken(refresh_token)
        self.expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires)

    def __str__(self):
        return '%s %s' % (self.type, self.token)

    def __repr__(self):
        return '<AccessToken %s: %s>' % (self.token, 'valid' if not self.is_expires else 'invalid')

    @property
    def is_expired(self):
        if self.expires > datetime.datetime.utcnow() + datetime.timedelta(seconds=60):
            return False
        else:
            return True


class QuestradeWrapper():
    api_version = 'v1'
    auth_endpoint_template = 'https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token=%s'
    access_token = None

    def __init__(self):
        self.refresh_token = RefreshToken.load()
        self._auth()

    def _auth(self):
        logging.info('Auth - Exchanging refresh token for new access token')
        auth_endpoint = self.auth_endpoint_template % self.refresh_token
        response = requests.get(auth_endpoint)
        if response.status_code != 200:
            print(response.status_code, response.content)
            raise QuestradeAuthException
        data = response.json()
        self.access_token = AccessToken(data['api_server'], data['access_token'], data['token_type'], data['refresh_token'], expires=data['expires_in'])
        self.refresh_token = self.access_token.refresh_token
        RefreshToken.dump(self.refresh_token)

    def _generate_endpoint(self, path, **params):
        if self._is_access_token_valid():
            self._auth()
        return '%s%s%s' % (self.access_token.api_server, self.api_version, path % params)

    def _simple_parse(self, data, name):
        return json.loads(data, object_hook=lambda d: namedtuple(name, d.keys(), rename=True)(*d.values()))

    def _is_access_token_valid(self):
        if self.access_token is None:
            return True
        else:
            if self.access_token.is_expired:
                return True
            else:
                return False
        
            self._auth()

    def _make_request(self, endpoint, **params):
        if self._is_access_token_valid():
            self._auth()
        response = requests.get(endpoint, params=params, headers={'Authorization': str(self.access_token)})
        if response.status_code != 200:
            print(response.status_code, response.content)
            raise QuestradeRequestException
        return response.content

    def accounts(self):
        logging.info('API Request - Accounts')
        endpoint = self._generate_endpoint('/accounts')
        content = self._make_request(endpoint)
        return self._simple_parse(content, 'Account').accounts

    def accounts_balances(self, account, type='combinedBalances', currency='CAD'):
        logging.info('API Request - Account Balance')
        endpoint = self._generate_endpoint('/accounts/%(account_id)s/balances', account_id=account.number)
        content = self._make_request(endpoint)
        return self._simple_parse(content, 'Balance').combinedBalances

    def accounts_positions(self, account):
        logging.info('API Request - Account Positions')
        endpoint = self._generate_endpoint('/accounts/%(account_id)s/positions', account_id=account.number)
        content = self._make_request(endpoint)
        return self._simple_parse(content, 'Position').positions

    def symbols(self, symbols):
        logging.info('API Request - Symbols')
        endpoint = self._generate_endpoint('/symbols')
        content = self._make_request(endpoint, names=','.join(symbols))
        return self._simple_parse(content, 'Symbol').symbols

    def markets_quotes(self, symbols):
        logging.info('API Request - Market Quotes')
        endpoint = self._generate_endpoint('/markets/quotes')
        params = {
            'ids': ','.join([str(symbol.symbolId) for symbol in symbols if symbol.isQuotable])
        }
        content = self._make_request(endpoint, **params)
        return self._simple_parse(content, 'Quote').quotes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Provide a new refresh token.',
    )
    parser.add_argument('-t', '--token', required=True)
    args = parser.parse_args()

    RefreshToken.dump(args.token)
