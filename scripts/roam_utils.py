# -*- coding: utf-8 -*-
"""
Title:        roam_utils.py
Description:  Utility functions for Roam Research API scripts
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-6
Version:      2.0
License:      MIT
"""

from datetime import datetime
import re

def get_roam_date_format(date):
    """
    Convert a date to the format Roam uses for daily pages.

    Args:
    date (datetime.date or str): The date to format. If a string is provided,
                                 it's assumed to be in the correct format already.

    Returns:
    str: The date in Roam's format (e.g., "July 6th, 2024")
    """
    if isinstance(date, str):
        # If it's already a string, assume it's in the correct format and return it
        return date

    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    day = date.day
    suffix = suffixes.get(day % 10, 'th') if day not in [11, 12, 13] else 'th'
    return date.strftime(f"%B {day}{suffix}, %Y")

def is_valid_date_string(date_string):
    """
    Check if a string is a valid date in YYYY-MM-DD format.

    Args:
    date_string (str): The string to check.

    Returns:
    bool: True if the string is a valid date, False otherwise.
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

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


