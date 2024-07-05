#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Add Block to Roam Page - add_block.py
Description:  A script to add a block to a specified page or today's daily page in Roam Research, optionally as a child of a parent block.
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-04
Version:      3.0
License:      MIT
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI, get_roam_date_format, process_block_text, q

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Initialize RoamAPI
ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')
roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Add a block to a page in Roam Research.")
	parser.add_argument("blocktext", help="The text content of the block to add.")
	parser.add_argument("-pg","--page", help="The page (pg) to add the block to. Can be a date (YYYY-MM-DD), a page title, or a page UID. If not provided, defaults to today's daily page.")
	parser.add_argument("-pb","--parent", help="The text of the parent block (pb) under which to nest the new block. If not found, it will be created.")
	parser.add_argument("-o","--order", default="last", choices=["first", "last"], help="Where to add the block (default: last)")

	args = parser.parse_args()

	roam.add_block_to_page(args.blocktext, args.page, args.parent, args.order)