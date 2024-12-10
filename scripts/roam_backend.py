"""
Roam Research API Client
Version: 1.2.0
Last Updated: 2024-12-09

An enhanced Python client for interacting with the Roam Research API.
Provides advanced functionality for querying and manipulating Roam graphs,
including block and page operations, batch processing, and template support.

Copyright (c) 2024
"""

from typing import Optional, Dict, Any, List, Union, Callable
import requests
import json
import re
import asyncio
import aiohttp
from datetime import datetime
from functools import lru_cache
from schema import Schema, Or, And, Use, Optional as SchemaOptional, SchemaError
from tenacity import retry, stop_after_attempt, wait_exponential

class RoamAPIError(Exception):
    """Base exception for Roam API errors"""
    pass

class RoamAuthError(RoamAPIError):
    """Raised when authentication fails"""
    pass

class RoamServerError(RoamAPIError):
    """Raised when server encounters an error"""
    pass

class RoamValidationError(RoamAPIError):
    """Raised when input validation fails"""
    pass

class RoamBackendClient:
    """Enhanced client for interacting with Roam Research API"""
    
    def __init__(self, token: str, graph: str, max_retries: int = 3, cache_size: int = 128):
        self.__token = token
        self.graph = graph
        self.__cache: Dict[str, Any] = {}
        self.__headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {token}',
            'x-authorization': f'Bearer {token}'
        }
        self.__base_url = 'https://api.roamresearch.com'
        self.max_retries = max_retries
        self.cache_size = cache_size
        self.__session = requests.Session()

    def __del__(self):
        self.__session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def __make_request(self, path: str, body: Dict[str, Any], method: str = 'POST') -> tuple:
        """Prepare request URL and headers with retry logic"""
        base_url = self.__cache.get(self.graph, self.__base_url)
        return (f"{base_url}{path}", method, self.__headers)

    def __handle_error(self, resp: requests.Response) -> None:
        """Enhanced error handling with detailed messages"""
        error_map = {
            400: lambda: RoamValidationError(f"Bad Request: {resp.json()}"),
            401: lambda: RoamAuthError("Invalid token or insufficient privileges"),
            403: lambda: RoamAuthError("Access forbidden - check graph permissions"),
            404: lambda: RoamAPIError("Resource not found"),
            429: lambda: RoamAPIError("Rate limit exceeded - please wait"),
            500: lambda: RoamServerError(f"Server Error: {resp.json()}"),
            503: lambda: RoamServerError("Graph not ready, please retry in a few seconds")
        }
        error_class = error_map.get(resp.status_code, lambda: RoamAPIError(f"Unknown error: {resp.status_code}"))
        raise error_class()

    @lru_cache(maxsize=128)
    def call(self, path: str, method: str, body: Dict[str, Any]) -> requests.Response:
        """Make API call with automatic redirect handling and caching"""
        url, method, headers = self.__make_request(path, body, method)
        resp = self.__session.post(url, headers=headers, json=body, allow_redirects=False)
        
        if resp.is_redirect or resp.is_permanent_redirect:
            location = resp.headers.get('Location')
            if not location:
                raise RoamAPIError("Redirect location not provided")
            
            match = re.search(r'https://(peer-\d+).*?:(\d+).*', location)
            if not match:
                raise RoamAPIError("Invalid redirect URL format")
            
            peer_n, port = match.groups()
            self.__cache[self.graph] = f'https://{peer_n}.api.roamresearch.com:{port}'
            return self.call(path, method, body)
        
        if not resp.ok:
            self.__handle_error(resp)
            
        return resp

    async def async_call(self, path: str, method: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous API call for better performance"""
        url, method, headers = self.__make_request(path, body, method)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as resp:
                if not resp.ok:
                    self.__handle_error(resp)
                return await resp.json()

    def batch_operation(self, operations: List[Dict[str, Any]]) -> List[int]:
        """Execute multiple operations in batch"""
        results = []
        for op in operations:
            path = f'/api/graph/{self.graph}/write'
            resp = self.call(path, 'POST', op)
            results.append(resp.status_code)
        return results

    def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search across the graph"""
        path = f'/api/graph/{self.graph}/q'
        search_query = f"""
        [:find (pull ?b [*])
         :where
         [?b :block/string ?string]
         [(re-pattern {"(?i)" if not case_sensitive else ""}{json.dumps(query)}) ?pattern]
         [(re-find ?pattern ?string)]]
        """
        resp = self.call(path, 'POST', {'query': search_query})
        return resp.json()['result']

    def get_references(self, page_title: str) -> List[Dict[str, Any]]:
        """Get all references to a page"""
        path = f'/api/graph/{self.graph}/q'
        query = f"""
        [:find (pull ?b [*])
         :where
         [?p :node/title "{page_title}"]
         [?b :block/refs ?p]]
        """
        resp = self.call(path, 'POST', {'query': query})
        return resp.json()['result']

    def create_from_template(self, template_name: str, replacements: Dict[str, str]) -> str:
        """Create content from a template"""
        template = self.get_template(template_name)
        for key, value in replacements.items():
            template = template.replace(f"{{${key}}}", value)
        return self.create_page({"page": {"title": replacements.get("title", "New Page"), "children": [{"string": template}]}})

    def backup_graph(self, path: str) -> None:
        """Backup entire graph to file"""
        path = f'/api/graph/{self.graph}/q'
        query = '[:find (pull ?e [*]) :where [?e :node/title]]'
        resp = self.call(path, 'POST', {'query': query})
        with open(path, 'w') as f:
            json.dump(resp.json()['result'], f)

    @lru_cache(maxsize=128)
    def get_template(self, template_name: str) -> str:
        """Get template content"""
        path = f'/api/graph/{self.graph}/q'
        query = f"""
        [:find (pull ?b [:block/string])
         :where
         [?p :node/title "Templates"]
         [?b :block/page ?p]
         [?b :block/string ?s]
         [(clojure.string/includes? ?s "{template_name}")]]
        """
        resp = self.call(path, 'POST', {'query': query})
        return resp.json()['result'][0]['string']

    def get_daily_notes(self, date: datetime) -> Dict[str, Any]:
        """Get daily notes for a specific date"""
        formatted_date = date.strftime("%m-%d-%Y")
        path = f'/api/graph/{self.graph}/q'
        query = f"""
        [:find (pull ?p [*])
         :where
         [?p :node/title "{formatted_date}"]]
        """
        resp = self.call(path, 'POST', {'query': query})
        return resp.json()['result'][0] if resp.json()['result'] else None

# Enhanced utility functions with improved validation and error handling
def q(client: RoamBackendClient, query: str, args: Optional[Dict[str, Any]] = None) -> Any:
    """Execute a Roam query with validation"""
    if not query.strip():
        raise RoamValidationError("Query cannot be empty")
    path = f'/api/graph/{client.graph}/q'
    body = {'query': query, 'args': args} if args else {'query': query}
    resp = client.call(path, 'POST', body)
    return resp.json()['result']

def pull(client: RoamBackendClient, pattern: str, eid: str) -> Any:
    """Pull data for a single entity with validation"""
    if not pattern or not eid:
        raise RoamValidationError("Pattern and EID are required")
    path = f'/api/graph/{client.graph}/pull'
    body = {'eid': eid, 'selector': pattern}
    resp = client.call(path, 'POST', body)
    return resp.json()['result']

def pull_many(client: RoamBackendClient, pattern: str, eids: List[str]) -> Any:
    """Pull data for multiple entities with validation"""
    if not pattern or not eids:
        raise RoamValidationError("Pattern and EIDs are required")
    path = f'/api/graph/{client.graph}/pull-many'
    body = {'eids': eids, 'selector': pattern}
    resp = client.call(path, 'POST', body)
    return resp.json()['result']

# Enhanced schemas with more validation
LOCATION_SCHEMA = Schema({
    'parent-uid': And(str, len),
    'order': Or(int, And(str, Use(int)))
})

BLOCK_SCHEMA = Schema({
    'string': And(str, len),
    SchemaOptional('uid'): And(str, len),
    SchemaOptional('open'): bool,
    SchemaOptional('heading'): And(int, lambda n: 0 <= n <= 3),
    SchemaOptional('text-align'): str,
    SchemaOptional('children-view-type'): And(str, lambda s: s in ['document', 'bullet', 'numbered'])
})

# Enhanced operations with validation and error handling
def create_block(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Create a new block with validation"""
    body['action'] = 'create-block'
    schema = Schema({'action': 'create-block', 'location': LOCATION_SCHEMA, 'block': BLOCK_SCHEMA})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def move_block(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Move an existing block with validation"""
    body['action'] = 'move-block'
    schema = Schema({'action': 'move-block', 'location': LOCATION_SCHEMA, 'block': {'uid': And(str, len)}})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def update_block(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Update an existing block with validation"""
    body['action'] = 'update-block'
    schema = Schema({'action': 'update-block', 'block': {
        SchemaOptional('string'): And(str, len),
        'uid': And(str, len),
        SchemaOptional('open'): bool,
        SchemaOptional('heading'): And(int, lambda n: 0 <= n <= 3),
        SchemaOptional('text-align'): str,
        SchemaOptional('children-view-type'): And(str, lambda s: s in ['document', 'bullet', 'numbered'])
    }})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def delete_block(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Delete a block with validation"""
    body['action'] = 'delete-block'
    schema = Schema({'action': 'delete-block', 'block': {'uid': And(str, len)}})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def create_page(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Create a new page with validation"""
    body['action'] = 'create-page'
    schema = Schema({'action': 'create-page', 'page': {
        SchemaOptional('uid'): And(str, len),
        'title': And(str, len),
        SchemaOptional('children-view-type'): And(str, lambda s: s in ['document', 'bullet', 'numbered'])
    }})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def update_page(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Update an existing page with validation"""
    body['action'] = 'update-page'
    schema = Schema({'action': 'update-page', 'page': {
        'uid': And(str, len),
        SchemaOptional('title'): And(str, len),
        SchemaOptional('children-view-type'): And(str, lambda s: s in ['document', 'bullet', 'numbered'])
    }})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def delete_page(client: RoamBackendClient, body: Dict[str, Any]) -> int:
    """Delete a page with validation"""
    body['action'] = 'delete-page'
    schema = Schema({'action': 'delete-page', 'page': {'uid': And(str, len)}})
    try:
        validated_body = schema.validate(body)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    path = f'/api/graph/{client.graph}/write'
    resp = client.call(path, 'POST', validated_body)
    return resp.status_code

def initialize_graph(inp: Dict[str, str]) -> RoamBackendClient:
    """Initialize a new Roam graph client with validation"""
    schema = Schema({'graph': And(str, len), 'token': And(str, len)})
    try:
        validated_input = schema.validate(inp)
    except SchemaError as e:
        raise RoamValidationError(str(e))
    return RoamBackendClient(validated_input['token'], validated_input['graph'])
