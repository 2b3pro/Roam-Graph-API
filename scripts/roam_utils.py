# -*- coding: utf-8 -*-
"""
Title:        roam_utils.py
Description:  Enhanced utility functions for Roam Research API scripts
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-12-09
Version:      3.3.0
License:      MIT
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union, Tuple, Callable
import logging
import re
import json
import asyncio
from functools import lru_cache, wraps
from dataclasses import dataclass
from roam_backend import (
    initialize_graph, q, create_page, create_block, 
    RoamAPIError, RoamValidationError
)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def validate_input(validator: Callable) -> Callable:
    """Decorator for input validation"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validator(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {str(e)}")
                raise RoamValidationError(str(e))
        return wrapper
    return decorator

@dataclass
class RoamBlock:
    """Data class for Roam block information"""
    uid: str
    string: str
    children: List['RoamBlock'] = None
    page: Optional[str] = None
    order: Optional[int] = None
    
    @classmethod
    def from_query_result(cls, result: Dict[str, Any]) -> 'RoamBlock':
        """Create RoamBlock instance from query result"""
        return cls(
            uid=result.get('uid', ''),
            string=result.get('string', ''),
            children=[cls.from_query_result(child) for child in result.get('children', [])],
            page=result.get('page', {}).get('title'),
            order=result.get('order')
        )

class DateUtils:
    """Date-related utility functions"""
    
    @staticmethod
    def is_valid_date_string(date_string: str) -> bool:
        """Enhanced date string validation"""
        if not isinstance(date_string, str):
            return False
            
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            return False
            
        try:
            year, month, day = map(int, date_string.split('-'))
            if not (1 <= month <= 12 and 1 <= day <= 31):
                return False
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_roam_date_format(date: Union[str, datetime]) -> str:
        """Convert date to Roam Research format"""
        if isinstance(date, str):
            return date
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        day = date.day
        suffix = suffixes.get(day % 10, 'th') if day not in [11, 12, 13] else 'th'
        return date.strftime(f"%B {day}{suffix}, %Y")

    @staticmethod
    def get_date_range(start_date: datetime, end_date: datetime) -> List[str]:
        """Get list of dates in Roam format between start and end dates"""
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(DateUtils.get_roam_date_format(current_date))
            current_date += timedelta(days=1)
        return date_list

class BlockUtils:
    """Block manipulation utilities"""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def extract_uid(text: str) -> Optional[str]:
        """Extract UID from text with caching"""
        if not isinstance(text, str):
            return None
            
        if len(text) == 13 and text.startswith("((") and text.endswith("))"):
            uid = text[2:-2]
            return uid if len(uid) == 9 else None
        elif len(text) == 9:
            return text
            
        return None

    @staticmethod
    def process_q_result(result: Any) -> Optional[str]:
        """Enhanced query result processing"""
        if result is None:
            return None
            
        if isinstance(result, (str, int)):
            return str(result)
            
        if isinstance(result, (list, tuple)):
            if not result:
                return None
            if len(result) == 1:
                if isinstance(result[0], (list, tuple)) and len(result[0]) == 1:
                    return str(result[0][0])
                return str(result[0])
            return str(result[0])
            
        return str(result)

    @staticmethod
    async def batch_process_blocks(client: Any, blocks: List[Dict[str, Any]], 
                                 operation: Callable) -> List[Dict[str, Any]]:
        """Process multiple blocks asynchronously"""
        results = []
        async def process_block(block):
            try:
                result = await operation(client, block)
                results.append({"success": True, "block": block, "result": result})
            except Exception as e:
                results.append({"success": False, "block": block, "error": str(e)})
                
        await asyncio.gather(*[process_block(block) for block in blocks])
        return results

class MarkdownConverter:
    """Utilities for converting between Roam markdown and traditional markdown"""
    
    @staticmethod
    def roam_to_markdown(text: str) -> str:
        """
        Convert Roam Research markdown to traditional markdown.
        
        Args:
            text (str): Text in Roam markdown format
            
        Returns:
            str: Text in traditional markdown format
            
        Examples:
            >>> MarkdownConverter.roam_to_markdown("Some ^^highlighted^^ text")
            'Some ==highlighted== text'
            >>> MarkdownConverter.roam_to_markdown("Some __italic__ text")
            'Some *italic* text'
            >>> MarkdownConverter.roam_to_markdown("^^nested __formatting__ test^^")
            '==nested *formatting* test=='
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
            
        # First handle nested formatting by converting italics
        text = re.sub(r'__([^_]+?)__', r'*\1*', text)
        
        # Then convert highlights
        text = re.sub(r'\^\^([^^]+?)\^\^', r'==\1==', text)
        
        return text
    
    @staticmethod
    def markdown_to_roam(text: str) -> str:
        """
        Convert traditional markdown to Roam Research markdown.
        
        Args:
            text (str): Text in traditional markdown format
            
        Returns:
            str: Text in Roam markdown format
            
        Examples:
            >>> MarkdownConverter.markdown_to_roam("Some ==highlighted== text")
            'Some ^^highlighted^^ text'
            >>> MarkdownConverter.markdown_to_roam("Some *italic* text")
            'Some __italic__ text'
            >>> MarkdownConverter.markdown_to_roam("==nested *formatting* test==")
            '^^nested __formatting__ test^^'
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
            
        # First handle nested formatting by converting italics
        text = re.sub(r'\*([^*]+?)\*', r'__\1__', text)
        
        # Then convert highlights
        text = re.sub(r'==([^=]+?)==', r'^^\1^^', text)
        
        return text
    
    @staticmethod
    def convert_all_markdown(text: str, to_roam: bool = True) -> str:
        """
        Convert all markdown elements between formats.
        
        Args:
            text (str): Input text
            to_roam (bool): If True, convert to Roam format. If False, convert to traditional
            
        Returns:
            str: Converted text
            
        Examples:
            >>> text = "Some ==highlighted== *italic* text with ==*nested* formatting=="
            >>> MarkdownConverter.convert_all_markdown(text, to_roam=True)
            'Some ^^highlighted^^ __italic__ text with ^^__nested__ formatting^^'
            >>> text = "Some ^^highlighted^^ __italic__ text with ^^__nested__ formatting^^"
            >>> MarkdownConverter.convert_all_markdown(text, to_roam=False)
            'Some ==highlighted== *italic* text with ==*nested* formatting=='
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
            
        # Process text in chunks to handle nested formatting correctly
        if to_roam:
            # First convert all italics
            text = re.sub(r'\*([^*]+?)\*', r'__\1__', text)
            # Then convert all highlights
            text = re.sub(r'==([^=]+?)==', r'^^\1^^', text)
        else:
            # First convert all italics
            text = re.sub(r'__([^_]+?)__', r'*\1*', text)
            # Then convert all highlights
            text = re.sub(r'\^\^([^^]+?)\^\^', r'==\1==', text)
            
        return text

    @staticmethod
    def roam_table_to_markdown(text: str) -> str:
        """
        Convert Roam Research table format to traditional markdown table.
        
        Args:
            text (str): Text in Roam table format
            
        Returns:
            str: Text in traditional markdown table format
            
        Examples:
            >>> text = '''- {{[[table]]}}
            ...     - Header1
            ...         - Row1Col1
            ...     - Header2
            ...         - Row1Col2'''
            >>> MarkdownConverter.roam_table_to_markdown(text)
            '| Header1 | Header2 |\\n|---------|----------|\\n| Row1Col1 | Row1Col2 |'
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Split into lines and clean up
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove the table declaration if present
        if lines and '{{[[table]]}}' in lines[0]:
            lines = lines[1:]
            
        # Parse the hierarchical structure
        table_data = []
        current_row = []
        current_depth = 0
        
        for line in lines:
            # Skip empty lines
            if not line:
                continue
                
            # Count leading spaces/dashes to determine depth
            depth = len(line) - len(line.lstrip('- '))
            content = line.lstrip('- ').strip()
            
            if depth == current_depth:  # New column in same row
                current_row.append(content)
            elif depth > current_depth:  # Child content
                if current_row:  # If we have a row in progress
                    current_row[-1] = content  # Replace parent with child content
            else:  # New row
                if current_row:
                    table_data.append(current_row)
                current_row = [content]
                
            current_depth = depth
            
        # Add the last row if it exists
        if current_row:
            table_data.append(current_row)
            
        # If no data was parsed, return empty string
        if not table_data:
            return ""
            
        # Create the markdown table
        # First row is headers
        headers = table_data[0]
        result = []
        
        # Add headers
        result.append("| " + " | ".join(headers) + " |")
        
        # Add separator
        result.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Add data rows
        for row in table_data[1:]:
            # Pad row if necessary
            while len(row) < len(headers):
                row.append("")
            result.append("| " + " | ".join(row) + " |")
            
        return "\n".join(result)

    @staticmethod
    def markdown_table_to_roam(text: str) -> str:
        """
        Convert traditional markdown table to Roam Research table format.
        
        Args:
            text (str): Text in traditional markdown table format
            
        Returns:
            str: Text in Roam table format
            
        Examples:
            >>> text = '''| Header1 | Header2 |
            ... |---------|----------|
            ... | Row1Col1 | Row1Col2 |'''
            >>> MarkdownConverter.markdown_table_to_roam(text)
            '''- {{[[table]]}}
                - Header1
                    - Row1Col1
                - Header2
                    - Row1Col2'''
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Split into lines and clean up
        lines = [line.strip() for line in text.split('\n')]
        
        # Need at least header row and separator
        if len(lines) < 2:
            return ""
            
        # Parse header row
        header_row = lines[0]
        if not header_row.startswith('|') or not header_row.endswith('|'):
            return ""
            
        # Extract headers
        headers = [h.strip() for h in header_row.strip('|').split('|')]
        
        # Skip separator row
        data_rows = []
        for line in lines[2:]:  # Skip header and separator rows
            if line.startswith('|') and line.endswith('|'):
                cells = [cell.strip() for cell in line.strip('|').split('|')]
                data_rows.append(cells)
                
        # Build Roam table format
        result = ['- {{[[table]]}}']
        
        # Add headers with their corresponding data
        for col_idx, header in enumerate(headers):
            result.append(f'\t- {header}')
            # Add data for this column
            for row in data_rows:
                if col_idx < len(row):
                    result.append(f'\t\t- {row[col_idx]}')
                else:
                    result.append('\t\t- ')  # Empty cell
                    
        return '\n'.join(result)

class GraphUtils:
    """Graph-level utilities"""
    
    @staticmethod
    @validate_input(lambda client, page_identifier: isinstance(page_identifier, str))
    def page_exists(client: Any, page_identifier: str) -> Tuple[bool, Optional[str]]:
        """Enhanced page existence check with validation"""
        if page_identifier.startswith('('):
            page_uid = page_identifier.strip('()')
            result = q(client, f'[:find ?title . :where [?e :block/uid "{page_uid}"] [?e :node/title ?title]]')
            processed_result = BlockUtils.process_q_result(result)
            return (bool(processed_result), page_uid if processed_result else None)
        else:
            page_title = page_identifier
            result = q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
            processed_result = BlockUtils.process_q_result(result)
            return (bool(processed_result), processed_result)

    @staticmethod
    def find_nested_block(client: Any, page_identifier: str, parent_string: str, 
                         target_string: str) -> Dict[str, Any]:
        """Enhanced nested block finder with better error handling"""
        try:
            if page_identifier.startswith('('):
                page_uid = page_identifier.strip('()')
                page_title_result = q(client, f'[:find ?title . :where [?e :block/uid "{page_uid}"] [?e :node/title ?title]]')
                page_title = BlockUtils.process_q_result(page_title_result)
                if not page_title:
                    raise RoamAPIError(f"Page with UID '{page_uid}' not found.")
            else:
                page_title = page_identifier
                page_uid_result = q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
                page_uid = BlockUtils.process_q_result(page_uid_result)
                if not page_uid:
                    raise RoamAPIError(f"Page '{page_title}' not found.")

            child_blocks = q(client, f'[:find ?child_uid ?child_string :where [?page :block/uid "{page_uid}"] [?page :block/children ?child] [?child :block/uid ?child_uid] [?child :block/string ?child_string]]')

            parent_block = next((block for block in child_blocks if parent_string in block[1]), None)
            if not parent_block:
                raise RoamAPIError(f"Parent block not found on page '{page_title}'")

            parent_uid, parent_content = parent_block

            parent_child_blocks = q(client, f'[:find ?child_uid ?child_string :where [?parent :block/uid "{parent_uid}"] [?parent :block/children ?child] [?child :block/uid ?child_uid] [?child :block/string ?child_string]]')

            target_block = next((block for block in parent_child_blocks if target_string in block[1]), None)
            if not target_block:
                raise RoamAPIError(f"Target block not found under parent block")

            target_uid, target_string = target_block

            return {
                "page_title": page_title,
                "page_uid": page_uid,
                "parent_content": parent_content,
                "parent_uid": parent_uid,
                "target_uid": target_uid,
                "target_content": target_string
            }
        except Exception as e:
            logger.error(f"Error in find_nested_block: {str(e)}")
            raise

class SearchUtils:
    """Advanced search utilities"""
    
    @staticmethod
    def search_blocks(client: Any, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for blocks matching query"""
        search_query = f'[:find (pull ?b [:block/string :block/uid {{:block/children ...}} {{:block/page [:node/title :block/uid]}}]) :where [?b :block/string ?string] [(re-pattern {"" if case_sensitive else "(?i)"}{json.dumps(query)}) ?pattern] [(re-find ?pattern ?string)]]'
        return q(client, search_query)

    @staticmethod
    def find_references(client: Any, page_title: str) -> List[Dict[str, Any]]:
        """Find all references to a page"""
        query = f'[:find (pull ?b [:block/string :block/uid {{:block/page [:node/title]}}]) :where [?p :node/title "{page_title}"] [?b :block/refs ?p]]'
        return q(client, query)

    @staticmethod
    def find_common_references(client: Any, page1: str, page2: str) -> List[Dict[str, Any]]:
        """Find blocks that reference both pages"""
        query = f'[:find (pull ?b [:block/string :block/uid {{:block/page [:node/title]}}]) :where [?p1 :node/title "{page1}"] [?p2 :node/title "{page2}"] [?b :block/refs ?p1] [?b :block/refs ?p2]]'
        return q(client, query)

class CacheUtils:
    """Cache management utilities"""
    
    @staticmethod
    def clear_caches() -> None:
        """Clear all LRU caches"""
        BlockUtils.extract_uid.cache_clear()
        
    @staticmethod
    @lru_cache(maxsize=128)
    def get_page_references(client: Any, page_title: str) -> List[Dict[str, Any]]:
        """Cached page reference lookup"""
        return SearchUtils.find_references(client, page_title)

def log_roam_operation(operation: str, status: str, details: Optional[str] = None) -> None:
    """Enhanced operation logging"""
    log_message = f"Roam operation: {operation} - Status: {status}"
    if details:
        log_message += f" - Details: {details}"
    logger.info(log_message)
