# RoamBackendClient

RoamBackendClient is a Python client for interacting with the Roam Research API. It provides a simple interface for performing operations such as creating pages, adding blocks, and querying data in your Roam Research graph.

## Features

- Create new pages in your Roam Research graph
- Add blocks to existing pages
- Query data using Roam's query language
- Error handling and logging

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/roam-backend-client.git
   cd roam-backend-client
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Set up your environment variables:
   Create a `.env` file in the root directory of the project and add your Roam Research API token and graph name:

   ```
   ROAM_API_TOKEN=your_api_token_here
   ROAM_GRAPH_NAME=your_graph_name_here
   ```

2. Import and initialize the client:

   ```python
   from client import initialize_graph, create_page, create_block, q

   client = initialize_graph({'token': 'your_api_token', 'graph': 'your_graph_name'})
   ```

3. Create a new page:

   ```python
   create_page_body = {
       'action': 'create-page',
       'page': {
           'title': 'My New Page'
       }
   }
   create_page_status = create_page(client, create_page_body)
   ```

4. Add a block to a page:

   ```python
   create_block_body = {
       'action': 'create-block',
       'location': {'parent-uid': 'page_uid', 'order': 0},
       'block': {'string': 'Block content'}
   }
   create_block_status = create_block(client, create_block_body)
   ```

5. Query data:

   ```python
   query = '[:find ?uid . :where [?e :node/title "My New Page"] [?e :block/uid ?uid]]'
   result = q(client, query)
   ```

## Example

Check out the `helloworld.py` script for a complete example of how to use the RoamBackendClient to create a page and add a block.

## Error Handling

The client includes basic error handling and logging. You can adjust the logging level in your scripts:

```python
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s at Line %(lineno)d')
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This client is not officially associated with Roam Research. Use at your own risk.