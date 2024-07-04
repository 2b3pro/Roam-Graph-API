# Roam Research API Utilities

This README provides instructions and examples for using the `roam_api_utils.py` module to interact with the Roam Research API.

## Setup

1. Ensure you have the required dependencies installed:
   ```
   pip install python-dotenv requests
   ```

2. Create a `.env` file in your project directory with your Roam API credentials:
   ```
   ROAM_API_TOKEN=your_api_token_here
   ROAM_GRAPH_NAME=your_graph_name_here
   ```

3. Place `client.py` and `roam_api_utils.py` in your project directory.

## Usage

First, import the `RoamAPI` class and initialize it with your credentials:

```python
import os
from dotenv import load_dotenv
from roam_api_utils import RoamAPI

load_dotenv()
ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)
```

Now you can use the various methods provided by the `RoamAPI` class.

## Examples

### Creating a Page

```python
new_page_title = "My New Page"
roam.create_page(new_page_title)
```

### Adding a Block to a Page

```python
roam.add_block("My New Page", "This is a new block")
roam.add_block("My New Page", "This is another block", order=1)  # Specify order (optional)
```

### Getting Page UID

```python
page_uid = roam.get_page_uid("My New Page")
print(f"Page UID: {page_uid}")
```

### Getting Block UIDs for a Page

```python
block_uids = roam.get_block_uids("My New Page")
print(f"Block UIDs: {block_uids}")
```

### Getting Block Content

```python
for uid in block_uids:
	content = roam.get_block_content(uid)
	print(f"Block content: {content}")
```

### Updating a Block

```python
roam.update_block(block_uids[0], "Updated block content")
```

### Deleting a Block

```python
roam.delete_block(block_uids[-1])  # Delete the last block
```

### Moving a Block

```python
new_parent_uid = roam.get_page_uid("Another Page")
roam.move_block(block_uids[0], new_parent_uid, 0)  # Move to the top of Another Page
```

### Searching Pages

```python
search_results = roam.search_pages("My New")
print(f"Pages containing 'My New': {search_results}")
```

### Getting Page References

```python
references = roam.get_page_references("My New Page")
print(f"Pages referencing 'My New Page': {references}")
```

### Creating a Daily Note

```python
roam.create_daily_note()  # Creates a note for today
roam.create_daily_note("05-15-2023")  # Creates a note for a specific date
```

### Getting Graph Structure

```python
graph_structure = roam.get_graph_structure()
print("Graph structure:")
for page in graph_structure:
	print(f"Page: {page[':node/title']}")
	for child in page.get(':block/children', []):
		print(f"  - {child[':block/string']}")
```

## Error Handling

Most methods will print an error message and return `None` or `False` if an operation fails. You can add try/except blocks in your code for more detailed error handling.

## Notes

- Some operations may take a moment to be reflected in the Roam graph. If you're not seeing expected changes immediately, try adding a small delay (e.g., `time.sleep(1)`) after operations.
- Be cautious when deleting or moving blocks, as these operations can't be easily undone through the API.
- Always test your scripts on a non-critical graph before running them on your main Roam database.

For more detailed information about the Roam Research API, refer to the official Roam Research documentation.