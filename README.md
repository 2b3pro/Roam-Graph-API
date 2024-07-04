# Roam Research Graph API Utilities

This package provides utilities for interacting with the Roam Research API.

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

### Creating a Page

```python
roam.create_page("New Page Title")
```

### Adding a Block

```python
page_uid = roam.get_page_uid("Page Title")
roam.add_block(page_uid, "Block content", order='last')
```

### Getting or Creating a Daily Note

```python
import datetime

today_uid = roam.get_or_create_daily_note()
specific_date_uid = roam.get_or_create_daily_note(datetime.datetime(2024, 7, 4))
```

### Processing Markdown Files

Use `process_markdown.py` to convert a markdown file into a Roam page with nested blocks:

```
python process_markdown.py input_file.md
```

### Searching the Roam Graph

Use `search_roam.py` to search for a page and get results in JSON or Markdown format:

```
python search_roam.py "Marcus Aurelius" --format json
python search_roam.py "Marcus Aurelius" --format markdown
```

## Notes

- Based on [Roam Research Backend SDKs](https://github.com/Roam-Research/backend-sdks)
- Some operations may take time to reflect in the Roam graph.
- Be cautious with delete or move operations, as they can't be easily undone via API.
- Test scripts on non-critical graphs before using on main databases.

For more information, refer to the [Roam Research API documentation](https://github.com/Roam-Research/backend-sdks).

README.md generated by Claude 3.5 Sonnet, last updated 2024-07-04 10:50 PT