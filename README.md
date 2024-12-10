# RoamBackendClient

RoamBackendClient is a Python client for interacting with the Roam Research API. It provides a comprehensive interface for performing operations such as creating pages, managing blocks, querying data, and converting between Roam and standard markdown formats in your Roam Research graph.

An abstraction of the underlying backend SDK provided by [Roam-Research](https://roamresearch.com) [backendSDKs-Python](https://github.com/Roam-Research/backend-sdks).

## Features

- Page Management

  - Create new pages with titles and content
  - Get page UIDs and content
  - Search pages by title or content
  - Get page references and backlinks
  - Import markdown files with YAML frontmatter

- Block Operations

  - Add blocks with rich text formatting
  - Create nested block structures
  - Batch create multiple blocks
  - Find and manage block UIDs
  - Process block content with TODO/DONE status

- Query Capabilities

  - Execute Datalog queries
  - Search across the graph
  - Get graph structure
  - Find common references between pages

- Date Handling

  - Support for daily notes
  - Date format conversion
  - Date range operations

- Format Conversion
  - Convert between Roam and standard markdown
  - Table format conversion
  - Text formatting conversion
  - Support for YAML frontmatter

For detailed information about utility functions and format conversions, see [scripts/README.md](scripts/README.md).

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

2. Basic Usage:

   ```python
   from scripts.roamresearch import RoamAPI

   # Initialize the client
   roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

   # Create a page
   roam.create_page("My New Page")

   # Add blocks to a page
   roam.add_block_to_page("This is a test block", "My New Page")
   roam.add_block_to_page("This is a nested block", "My New Page", "This is a test block")
   ```

3. Working with Daily Notes:

   ```python
   # Get or create today's daily note
   today_uid = roam.get_or_create_daily_note()

   # Add content to today's note
   roam.add_block_to_page("Meeting notes for today", today_uid)
   ```

4. Importing Markdown:

   ```python
   # Import a markdown file with YAML frontmatter
   success, message = roam.import_markdown_file("path/to/markdown.md")
   ```

5. Searching and Querying:

   ```python
   # Search for pages
   results = roam.search_pages("search term")

   # Get page references
   refs = roam.get_page_references("Page Title")

   # Get page content
   content = roam.get_page("Page Title", prefix="", output_format="markdown")
   ```

## Error Handling

The client includes comprehensive error handling and logging. You can adjust the logging level in your scripts:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This client is not officially associated with Roam Research. Use at your own risk.
