"""
Title: Roam Research Backend Client SDK
Description:
Author: Roam Research
Modified by: Ian Shen
Version: 1.1.0
"""

import requests
import json
import re
from schema import Schema, Or, And, Use, Optional

class RoamBackendClient:
    def __init__(self, token, graph):
        self.__token = token
        self.graph = graph
        self.__cache = {}
        self.base_url = 'https://api.roamresearch.com'

    def __make_request(self, path, body, method='POST'):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {self.__token}',
            'x-authorization': f'Bearer {self.__token}'
        }
        url = f"{self.__cache.get(self.graph, self.base_url)}{path}"
        return url, method, headers

    def call(self, path, method, body):
        url, method, headers = self.__make_request(path, body, method)
        resp = requests.post(url, headers=headers, json=body, allow_redirects=False)

        if resp.is_redirect or resp.is_permanent_redirect:
            if 'Location' in resp.headers:
                mtch = re.search(r'https://(peer-\d+).*?:(\d+).*', resp.headers['Location'])
                if mtch:
                    peer_n, port = mtch.groups()
                    self.__cache[self.graph] = f'https://{peer_n}.api.roamresearch.com:{port}'
                    return self.call(path, method, body)
            raise Exception('Unexpected redirect without Location header')

        if not resp.ok:
            error_messages = {
                500: 'Internal Server Error',
                400: 'Bad Request',
                401: "Invalid token or insufficient privileges",
                503: "Graph not ready, please retry in a few seconds"
            }
            error_message = error_messages.get(resp.status_code, f'Unexpected error: {resp.status_code}')
            raise Exception(f'Error (HTTP {resp.status_code}): {error_message}')

        return resp

def q(client: RoamBackendClient, query: str, args = None):
    path = '/api/graph/' + client.graph + '/q'
    body = {'query': query}
    if args is not None:
        body['args'] = args
    resp = client.call(path, 'POST', body)
    result = resp.json()
    return result['result']

def pull(client: RoamBackendClient, pattern: str, eid: str):
    path = '/api/graph/' + client.graph + '/pull'
    body = {'eid': eid, 'selector': pattern}
    resp = client.call(path, 'POST', body)
    result = resp.json()
    return result['result']

def pull_many(client: RoamBackendClient, pattern: str, eids: str):
    path = '/api/graph/' + client.graph + '/pull-many'
    body = {'eids': eids, 'selector': pattern}
    resp = client.call(path, 'POST', body)
    result = resp.json()
    return result['result']

roam_block_location = Schema({'parent-uid': str, 'order': Or(int, str)})

roam_block = Schema({'string': str, Optional('uid'): str, Optional('open'): bool, Optional('heading'): int, Optional('text-align'): bool, Optional('children-view-type'): str})

roam_create_block = Schema({Optional('action'): And(str, lambda s: s=='create-block'), 'location': roam_block_location, 'block': roam_block})

def create_block(client: RoamBackendClient, body):
    body['action'] = 'create-block'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_create_block.validate(body))
    return resp.status_code

roam_move_block = Schema({Optional('action'): And(str, lambda s: s=='move-block'), 'location': roam_block_location, 'block': {'uid': str}})

def move_block(client: RoamBackendClient, body):
    body['action'] = 'move-block'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_move_block.validate(body))
    return resp.status_code

roam_update_block = Schema({Optional('action'): And(str, lambda s: s=='update-block'), 'block': {Optional('string'): str, 'uid': str, Optional('open'): bool, Optional('heading'): int, Optional('text-align'): bool, Optional('children-view-type'): str}})

def update_block(client: RoamBackendClient, body):
    body['action'] = 'update-block'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_update_block.validate(body))
    return resp.status_code

roam_delete_block = Schema({Optional('action'): And(str, lambda s: s=='delete-block'), 'block': {'uid': str}})

def delete_block(client: RoamBackendClient, body):
    body['action'] = 'delete-block'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_delete_block.validate(body))
    return resp.status_code

roam_create_page = Schema({Optional('action'): And(str, lambda s: s=='create-page'), 'page': {Optional('uid'): str, 'title': str, Optional('children-view-type'): str}})

def create_page(client: RoamBackendClient, body):
    body['action'] = 'create-page'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_create_page.validate(body))
    return resp.status_code

roam_update_page = Schema({Optional('action'): And(str, lambda s: s=='update-page'), 'page': {'uid': str, Optional('title'): str, Optional('children-view-type'): str}})

def update_page(client: RoamBackendClient, body):
    body['action'] = 'update-page'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_update_page.validate(body))
    return resp.status_code

roam_delete_page = Schema({Optional('action'): And(str, lambda s: s=='delete-page'), 'page': {'uid': str}})

def delete_page(client: RoamBackendClient, body):
    body['action'] = 'delete-page'
    path = '/api/graph/' + client.graph + '/write'
    resp = client.call(path, 'POST', roam_delete_page.validate(body))
    return resp.status_code

init_graph = Schema({'graph': str, 'token': str})

def initialize_graph(inp):
    Schema({'graph': str, 'token': str}).validate(inp)
    return RoamBackendClient(inp['token'], inp['graph'])