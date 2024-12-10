# Roam Research Utilities

This directory contains utility functions for working with Roam Research data and formats.

## MarkdownConverter

The `MarkdownConverter` class provides utilities for converting between Roam Research markdown and traditional markdown formats.

### Table Conversion

#### Converting Roam Tables to Markdown

```python
from roam_utils import MarkdownConverter

# Example Roam table
roam_table = """- {{[[table]]}}
    - Header1
        - Row1Col1
        - Row2Col1
    - Header2
        - Row1Col2
        - Row2Col2"""

# Convert to traditional markdown table
markdown_table = MarkdownConverter.roam_table_to_markdown(roam_table)
print(markdown_table)
```

Output:

```markdown
| Header1  | Header2  |
| -------- | -------- |
| Row1Col1 | Row1Col2 |
| Row2Col1 | Row2Col2 |
```

#### Converting Markdown Tables to Roam

```python
from roam_utils import MarkdownConverter

# Example markdown table
markdown_table = """| Header1 | Header2 |
|---------|---------|
| Row1Col1 | Row1Col2 |
| Row2Col1 | Row2Col2 |"""

# Convert to Roam table format
roam_table = MarkdownConverter.markdown_table_to_roam(markdown_table)
print(roam_table)
```

Output:

```
- {{[[table]]}}
    - Header1
        - Row1Col1
        - Row2Col1
    - Header2
        - Row1Col2
        - Row2Col2
```

### Text Formatting Conversion

#### Converting Roam Formatting to Markdown

```python
from roam_utils import MarkdownConverter

# Convert highlighted and italic text
roam_text = "Some ^^highlighted^^ and __italic__ text"
markdown_text = MarkdownConverter.roam_to_markdown(roam_text)
print(markdown_text)  # Output: "Some ==highlighted== and *italic* text"

# Convert nested formatting
roam_text = "^^nested __formatting__ test^^"
markdown_text = MarkdownConverter.roam_to_markdown(roam_text)
print(markdown_text)  # Output: "==nested *formatting* test=="
```

#### Converting Markdown Formatting to Roam

```python
from roam_utils import MarkdownConverter

# Convert highlighted and italic text
markdown_text = "Some ==highlighted== and *italic* text"
roam_text = MarkdownConverter.markdown_to_roam(markdown_text)
print(roam_text)  # Output: "Some ^^highlighted^^ and __italic__ text"

# Convert nested formatting
markdown_text = "==nested *formatting* test=="
roam_text = MarkdownConverter.markdown_to_roam(markdown_text)
print(roam_text)  # Output: "^^nested __formatting__ test^^"
```

## BlockUtils

The `BlockUtils` class provides utilities for working with Roam blocks.

### Extracting UIDs

```python
from roam_utils import BlockUtils

# Extract UID from reference
uid = BlockUtils.extract_uid("((abc123xyz))")
print(uid)  # Output: "abc123xyz"

# Extract standalone UID
uid = BlockUtils.extract_uid("abc123xyz")
print(uid)  # Output: "abc123xyz"
```

### Processing Query Results

```python
from roam_utils import BlockUtils

# Process various query result types
result = BlockUtils.process_q_result(["value"])
print(result)  # Output: "value"

result = BlockUtils.process_q_result([["nested_value"]])
print(result)  # Output: "nested_value"
```

## GraphUtils

The `GraphUtils` class provides utilities for working with the Roam graph.

### Checking Page Existence

```python
from roam_utils import GraphUtils

# Check if page exists by title
exists, uid = GraphUtils.page_exists(client, "Page Title")

# Check if page exists by UID
exists, title = GraphUtils.page_exists(client, "((abc123xyz))")
```

### Finding Nested Blocks

```python
from roam_utils import GraphUtils

# Find nested block
result = GraphUtils.find_nested_block(
    client,
    "Page Title",
    "Parent Block Content",
    "Target Block Content"
)
```

## SearchUtils

The `SearchUtils` class provides utilities for searching the Roam graph.

### Searching Blocks

```python
from roam_utils import SearchUtils

# Search for blocks with case-insensitive matching
results = SearchUtils.search_blocks(client, "search term", case_sensitive=False)

# Find references to a page
refs = SearchUtils.find_references(client, "Page Title")

# Find common references between two pages
common_refs = SearchUtils.find_common_references(client, "Page1", "Page2")
```

## DateUtils

The `DateUtils` class provides utilities for working with dates in Roam format.

### Date Formatting

```python
from roam_utils import DateUtils
from datetime import datetime

# Convert date to Roam format
date = datetime(2024, 12, 9)
roam_date = DateUtils.get_roam_date_format(date)
print(roam_date)  # Output: "December 9th, 2024"

# Get date range in Roam format
start_date = datetime(2024, 12, 9)
end_date = datetime(2024, 12, 11)
dates = DateUtils.get_date_range(start_date, end_date)
```

## CacheUtils

The `CacheUtils` class provides utilities for managing caches.

### Cache Management

```python
from roam_utils import CacheUtils

# Clear all LRU caches
CacheUtils.clear_caches()

# Get cached page references
refs = CacheUtils.get_page_references(client, "Page Title")
```
