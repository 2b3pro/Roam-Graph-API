# -*- coding: utf-8 -*-
"""
Title:        roam_utils.py
Description:  Utility functions for Roam Research API scripts
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-6
Version:      2.2
License:      MIT
"""

from datetime import datetime
import logging
import re
from client import initialize_graph, q, create_page, create_block

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_roam_operation(operation, status, details=None):
    """Log Roam Research operations."""
    log_message = f"Roam operation: {operation} - Status: {status}"
    if details:
        log_message += f" - Details: {details}"
    logger.info(log_message)

def get_roam_date_format(date):
    if isinstance(date, str):
        return date
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    day = date.day
    suffix = suffixes.get(day % 10, 'th') if day not in [11, 12, 13] else 'th'
    return date.strftime(f"%B {day}{suffix}, %Y")

def process_block_text(block_text):
    """
    Cleans up text for import into Roam:
        - Strips any trailing whitespaces
        - Convert to Roam Research-flavored markdown for italics, highlights.
        - Replaces TODO/DONE codes
        - Replace literal '\n' with actual newline characters
    """

    block_text = block_text.strip()

    # Convert to Roam italics markdown and replace TODO/DONE codes
    patterns_replacements = [
        (r'\*(.*?)\*', r'__\1__'),
        (r'\[ ?\]', r'{{[[TODO]]}}'),
        (r'\[x\]', r'{{[[DONE]]}}')
    ]

    for pattern, replacement in patterns_replacements:
        block_text = re.sub(pattern, replacement, block_text)

    # Replace ~~ with ^^
        block_text = block_text.replace('~~', '^^')

    # Replace literal '\n' with actual newline characters
    block_text = block_text.replace('\\n', '\n')

    return block_text

# Functions requiring the client

def page_exists(client, page_identifier):
    """
    Check if a page exists in the Roam Research graph.

    This function can handle both page titles and page UIDs as identifiers.
    If a UID is provided, it should be wrapped in parentheses.

    Parameters:
    client (RoamBackendClient): The initialized Roam API client object.
    page_identifier (str): Either the page title or the page UID (wrapped in parentheses).
                           Examples:
                           - "My Page Title"
                           - "(abcd1234)"

    Returns:
    tuple: A tuple containing two elements:
           1. exists (bool): True if the page exists, False otherwise.
           2. uid (str or None): The UID of the page if it exists, None if it doesn't.

    Example usage:
    exists, uid = page_exists(client, "My Page Title")
    if exists:
        print(f"Page exists with UID: {uid}")
    else:
        print("Page does not exist")

    exists, uid = page_exists(client, "(abcd1234)")
    if exists:
        print(f"Page with UID abcd1234 exists")
    else:
        print("No page found with the given UID")
    """
    if page_identifier.startswith('('):  # UID provided
        page_uid = page_identifier.strip('()')
        result = q(client, f'[:find ?title . :where [?e :block/uid "{page_uid}"] [?e :node/title ?title]]')
        return (bool(result), page_uid if result else None)
    else:  # Page title provided
        page_title = page_identifier
        result = q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
        return (bool(result), result[0] if result else None)

def find_nested_block(client, page_identifier, parent_string, target_string):
    """
    Find a nested block within a Roam Research graph.

    :param client: The Roam Research client object
    :param page_identifier: Either the page title or UID (wrapped in parentheses)
    :param parent_string: String to identify the parent block
    :param target_string: String to find in the child block
    :return: A dictionary with the results or an error message
    """
    # Step 1: Determine if we're dealing with a page title or UID
    if page_identifier.startswith('('):  # Assuming UIDs are wrapped in parentheses
        page_uid = page_identifier.strip('()')
        page_title_result = q(client,f'[:find ?title :where [?e :block/uid "{page_uid}"] [?e :node/title ?title]]')
        page_title = page_title_result[0][0] if page_title_result else "Unknown"
    else:
        page_title = page_identifier
        page_uid_result = q(client,f'[:find ?uid :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
        if not page_uid_result:
            return {"error": f"Page '{page_title}' not found."}
        page_uid = page_uid_result[0][0]

    # Step 2: Find all child blocks of the page
    child_blocks = q(client,f'[:find ?child_uid ?child_string :where [?page :block/uid "{page_uid}"] [?page :block/children ?child] [?child :block/uid ?child_uid] [?child :block/string ?child_string]]')

    # Step 3: Find the parent block
    parent_block = next((block for block in child_blocks if parent_string in block[1]), None)
    if not parent_block:
        return {"error": f"No block containing '{parent_string}' found on page '{page_title}' (UID: {page_uid})."}

    parent_uid, parent_content = parent_block

    # Step 4: Find all child blocks of the parent block
    parent_child_blocks = q(client,f'[:find ?child_uid ?child_string :where [?parent :block/uid "{parent_uid}"] [?parent :block/children ?child] [?child :block/uid ?child_uid] [?child :block/string ?child_string]]')

    # Step 5: Find the target block
    target_block = next((block for block in parent_child_blocks if target_string in block[1]), None)
    if not target_block:
        return {"error": f"No block containing '{target_string}' found under the parent block on page '{page_title}' (UID: {page_uid})."}

    target_uid, target_string = target_block

    return {
        "page_title": page_title,
        "page_uid": page_uid,
        "parent_content": parent_content,
        "parent_uid": parent_uid,
        "target_uid": target_uid,
        "target_content": target_string
    }

