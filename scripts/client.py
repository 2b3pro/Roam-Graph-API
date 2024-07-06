import requests
import json
import re
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class RoamBackendClient:
    def __init__(self, token, graph):
        self.__token = token
        self.graph = graph
        self.__cache = {}

    def __make_request(self, path, body, method = None):
        method = 'POST' if method is None else method
        if self.graph in self.__cache:
            base_url = self.__cache[self.graph]
        else:
            base_url = 'https://api.roamresearch.com'
        return (base_url + path, method, {'Content-Type': 'application/json; charset=utf-8', 'Authorization': 'Bearer ' + self.__token, 'x-authorization': 'Bearer ' + self.__token })

    def call(self, path, method, body):
        url, method, headers = self.__make_request(path, body, method)
        resp = requests.post(url, headers=headers, json=body, allow_redirects=False)
        if resp.is_redirect or resp.is_permanent_redirect:
            if 'Location' in resp.headers:
                mtch = re.search(r'https://(peer-\d+).*?:(\d+).*', resp.headers['Location'])
                if mtch is None:
                    raise Exception('Unexpected redirect format')
                peer_n, port = mtch.groups()
                self.__cache[self.graph] = redirect_url = 'https://' + peer_n + '.api.roamresearch.com:' + port
                return self.call(path, method, body)
            else:
                raise Exception('Redirect without Location header')
        if not resp.ok:
            if resp.status_code == 500:
                raise Exception('Error (HTTP 500): ' + str(resp.json()))
            elif resp.status_code == 400:
                raise Exception('Error (HTTP 400): ' + str(resp.json()))
            elif resp.status_code == 401:
                raise Exception("Invalid token or token doesn't have enough privileges.")
            else:
                raise Exception('Error (HTTP 503): Your graph is not ready yet for a request, please retry in a few seconds.')
        return resp

def q(client: RoamBackendClient, query: str, args = None):
    path = '/api/graph/' + client.graph + '/q'
    body = {'query': query}
    if args is not None:
        body['args'] = args
    resp = client.call(path, 'POST', body)
    result = resp.json()
    return result['result']

def create_block(client: RoamBackendClient, body):
    body['action'] = 'create-block'
    path = '/api/graph/' + client.graph + '/write'
    try:
        resp = client.call(path, 'POST', body)
        return resp.status_code
    except Exception as e:
        logging.error(f"Error in create_block: {str(e)}")
        logging.error(f"Request body: {json.dumps(body, indent=2)}")
        raise

def initialize_graph(inp):
    return RoamBackendClient(inp['token'], inp['graph'])

# ... (you can add other functions like update_block, delete_block, etc. as needed)