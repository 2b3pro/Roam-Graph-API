# Changelog

All notable changes to this project will be documented in this file.

## [3.3.0] - 2024-12-09

### Added

- New table conversion methods in MarkdownConverter class:
  - roam_table_to_markdown: Converts Roam-flavored tables to traditional markdown
  - markdown_table_to_roam: Converts traditional markdown tables to Roam format
- Support for complex table structures with nested content
- Comprehensive documentation in scripts/README.md
- Detailed examples for all utility functions

### Changed

- Enhanced MarkdownConverter class with table handling capabilities
- Improved parsing of nested bullet structures
- Better handling of empty cells and table alignment

### Fixed

- Table structure preservation during conversion
- Proper indentation in Roam table output
- Consistent handling of table headers and separators

## [3.1.0] - 2024-12-09

### Added

- New MarkdownConverter class for bidirectional markdown format conversion
- Support for converting between Roam and traditional markdown:
  - Highlights (^^text^^ ↔ ==text==)
  - Italics (**text** ↔ _text_)
- Proper handling of nested formatting
- Comprehensive docstring examples for all conversion methods
- Batch conversion method for processing multiple elements

### Changed

- Moved markdown conversion methods to dedicated MarkdownConverter class
- Improved handling of nested markdown elements
- Enhanced regex patterns for more accurate conversions
- Cleaned up file structure and organization

### Fixed

- Query string formatting in SearchUtils
- Complex query handling
- Error propagation in nested operations
- Date validation edge cases
- Cache management consistency

## [1.2.0] - 2024-12-09

### Added

- Asynchronous API support using aiohttp
- Connection pooling with requests.Session
- LRU caching for frequently accessed data
- Batch operations support for multiple operations
- Graph-wide search functionality
- Template system with variable replacement
- Graph backup/restore functionality
- Reference tracking capabilities
- Daily notes support
- Enhanced input validation with detailed error messages
- Retry logic for transient failures using tenacity

### Changed

- Improved error handling with more specific error types
- Enhanced schema validation with stricter rules
- Optimized request handling with connection reuse
- Updated validation to include comprehensive type checks

### Fixed

- Improved error message clarity
- Enhanced validation for optional parameters
- Better handling of redirect responses

## [1.1.0] - 2024-12-09

### Added

- Custom exception classes for better error handling
- Comprehensive type hints throughout the codebase
- Detailed docstrings for all classes and methods
- Dedicated error handling method

### Changed

- Consolidated schema definitions to reduce code duplication
- Improved caching mechanism with better type organization
- Optimized string formatting using f-strings
- Enhanced header management in RoamBackendClient
- Improved error messages with specific descriptions

### Fixed

- Removed redundant string concatenations
- Replaced placeholder TODOs with proper error handling
