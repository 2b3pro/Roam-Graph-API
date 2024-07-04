#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Add Nested Block - add_nested_blocks.py
Description:  An example script demonstrating how to add a block to a page.
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-04
Version:      1.0
License:      MIT
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def add_nested_blocks_to_daily_note():
	# Initialize RoamAPI
	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

	# Get or create today's daily note
	daily_note_uid = roam.get_or_create_daily_note()

	# Define the nested blocks structure
	nested_blocks = [
		{
			"string": "This is the first block",
			"children": [
				{"string": "This is a child of the first block"},
				{
					"string": "This is another child of the first block",
					"children": [
						{"string": "This is a grandchild block"}
					]
				}
			]
		},
		{
			"string": "This is the second main block",
			"children": [
				{"string": "This is a child of the second block"}
			]
		}
	]

	# Add the nested blocks to the daily note
	success = roam.add_nested_blocks(daily_note_uid, nested_blocks)

	if success:
		print(f"Successfully added nested blocks to today's daily note")
	else:
		print(f"Failed to add nested blocks to today's daily note")

if __name__ == "__main__":
	add_nested_blocks_to_daily_note()