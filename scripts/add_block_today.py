#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Add Block to Daily Page - add_block_today.py
Description:  An example script demonstrating how to add a block to a page.
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-04
Version:      1.0
License:      MIT
"""

import os
import sys
import datetime
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def add_to_daily_note(content, order='last'):
	# Initialize RoamAPI
	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

	# Get or create today's daily note
	daily_note_uid = roam.get_or_create_daily_note()

	# Add the new block to the daily note
	success = roam.add_block(daily_note_uid, content, order)

	if success:
		print(f"Successfully added new block to today's daily note")
	else:
		print(f"Failed to add block to today's daily note")

if __name__ == "__main__":
	# You can change this content to whatever you want to add to your daily note
	new_block_content = "This is a new block added via the [[Roam API]]!"

	# You can change the order to 'first', 'last', or a number (0, 1, 2, etc.)
	add_to_daily_note(new_block_content, order='last')