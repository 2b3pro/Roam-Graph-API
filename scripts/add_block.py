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
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI, q

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
	parser.add_argument("-pg","--page", help="The page to add the block to. Can be a date (YYYY-MM-DD), a page title, or a page UID. If not provided, defaults to today's daily page.")
	parser.add_argument("-pb","--parent", help="The text of the parent block under which to nest the new block. If not found, it will be created.")
	parser.add_argument("-o","--order", default="last", choices=["first", "last"], help="Where to add the block (default: last)")

args = parser.parse_args()

# Process the block text
processed_block_text = roam.process_block_text(args.blocktext)
block_lines = processed_block_text.split('\n')

# Get or create the page UID
page_uid = roam.get_or_create_page_uid(args.page)
if not page_uid:
	logging.error(f"Could not find or create page: {args.page}")
	sys.exit(1)

if args.parent:
	# Find or create the parent block
	parent_uid = roam.find_or_create_parent_block(page_uid, args.parent)
	if parent_uid is None:
		logging.error(f"Could not find or create parent block: {args.parent}")
		sys.exit(1)
else:
	parent_uid = page_uid

# Prepare blocks for batch creation
blocks = [{"content": line.strip()} for line in block_lines if line.strip()]

# Use batch creation
logging.info(f"Adding {len(blocks)} blocks to the page")
roam.batch_create_blocks(parent_uid, blocks)

logging.info("Script completed successfully")