# Roam Research API Utilities

This package provides utilities for interacting with Roam Research graphs via the Backends API. Not official.

## Setup

1. Install required dependencies:
   ```
   pip install python-dotenv requests
   ```

2. Create a `.env` file in your project directory:
   ```
   ROAM_API_TOKEN=your_api_token_here
   ROAM_GRAPH_NAME=your_graph_name_here
   ```

3. Place `client.py` and `roam_api_utils.py` in your project directory.

## Usage

Import and initialize the `RoamAPI` class:

```python
from roam_api_utils import RoamAPI
from dotenv import load_dotenv
import os

load_dotenv()
roam = RoamAPI(os.getenv('ROAM_GRAPH_NAME'), os.getenv('ROAM_API_TOKEN'))
```

## Features

### 1. Adding a Block to a Page (add_block.py)

This script allows you to add a block to a specific page or today's daily page in Roam Research, optionally as a child of a parent block.

Usage:
```
python add_block.py --page "My Page" --block "This is a new block" --parent "Optional parent block" --order last
```

- `--page`: The page to add the block to. Can be a date (YYYY-MM-DD), a page title, or a page UID. If not provided, defaults to today's daily page.
- `--block`: The text content of the block to add.
- `--parent`: (Optional) The text of the parent block under which to nest the new block. If not found, it will be created.
- `--order`: (Optional) Where to add the block ("first" or "last", default: last).

### 2. Processing and Importing Markdown Files (import_markdown.py)

This script allows you to process a markdown file and add its content to a Roam Research page. See sample [Markdown file](./sample-md.md).

Usage:
```
python process_markdown.py path/to/your/markdown_file.md
```

### 3. Processing and Importing JSON Files (import_json.py)

This script parses a JSON file and adds its content to a Roam Research page. For a sample JSON structure, see [this sample](./README.md).

Usage:
```
python import_json.py path/to/your/json_file.json
```

### 4. Searching Roam (search_roam.py)

This script allows you to search for a page in your Roam graph and retrieve its content.

Usage:
```
python search_roam.py "Page Title" --format json --output-file output.json
```

- `"Page Title"`: The title of the page to search for.
- `--format`: (Optional) Output format, either "json" or "markdown" (default: json).
- `--output-file`: (Optional) Path to save the output. If not provided, prints to stdout.

## Other RoamAPI Features

The `RoamAPI` class provides several methods for interacting with your Roam graph:

1. `create_page(title)`: Create a new page with the given title.
2. `get_or_create_daily_note(date=None)`: Get or create a daily note for the given date (or today if not specified).
3. `add_block(parent_uid, content, order='last')`: Add a block to a page or another block using its UID.
4. `get_last_block_uid(parent_uid)`: Get the UID of the last block added to a page or block.
5. `add_nested_blocks(parent_uid, blocks, order='last')`: Add nested blocks to a page or another block.
6. `add_markdown_to_roam(file_path)`: Process a markdown file and add its content to Roam.
7. `import_json_to_page(json_data, page_title=None)`: Import JSON data to a Roam page.
8. `import_json_file_to_page(file_path, page_title=None)`: Import JSON file to a Roam page.
9. `get_page_uid(page_title)`: Get the UID of a page by its title.
10. `get_block_uids(page_title)`: Get the UIDs of all blocks on a page.
11. `get_block_content(block_uid)`: Get the content of a block by its UID.
12. `update_block(block_uid, new_content)`: Update the content of a block.
13. `delete_block(block_uid)`: Delete a block by its UID.
14. `move_block(block_uid, new_parent_uid, new_order)`: Move a block to a new parent and/or position.
15. `search_pages(search_string)`: Search for pages containing the given string.
16. `get_page_references(page_title)`: Get all pages that reference the given page.
17. `get_page_content(page_uid)`: Get the content of a page by its UID.
18. `get_graph_structure()`: Get a high-level structure of the graph (pages and their immediate children).

## Notes

- Using [Roam Research's Roam Backend Client](https://github.com/Roam-Research/backend-sdks)
- Some operations may take time to reflect in the Roam graph.
- Be cautious with delete or move operations, as they can't be easily undone via API.
- Test scripts on non-critical graphs before using on main databases.

For more information, refer to the [Roam Research API documentation](https://github.com/Roam-Research/backend-sdks).

README.md last updated 2024-07-04