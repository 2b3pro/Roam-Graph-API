#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Add Block to Roam Page - add_block.py
Description:  A script to add a block to a specified page or today's daily page in Roam Research, optionally as a child of a parent block.
Author:       Ian Shen (updated by Assistant)
Email:        2b3pro@gmail.com
Date:         2024-07-06
Version:      4.0
License:      MIT
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import logging
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import initialize_graph, create_page, create_block, q

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s at Line %(lineno)d')

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

def get_or_create_page_uid(client, page_title):
	query = f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]'
	page_uid = q(client, query)

	if not page_uid:
		logging.info(f"Page '{page_title}' not found. Creating it.")
		create_page_body = {
			'action': 'create-page',
			'page': {'title': page_title}
		}
		create_page_status = create_page(client, create_page_body)
		if create_page_status == 200:
			page_uid = q(client, query)
		else:
			logging.error(f"Failed to create page '{page_title}'. Status code: {create_page_status}")
			return None

	return page_uid

def find_or_create_parent_block(client, page_uid, parent_text):
	query = f'[:find ?uid . :where [?e :block/uid "{page_uid}"] [?e :block/children ?c] [?c :block/string "{parent_text}"] [?c :block/uid ?uid]]'
	parent_uid = q(client, query)

	if not parent_uid:
		logging.info(f"Parent block '{parent_text}' not found. Creating it.")
		create_block_body = {
			'action': 'create-block',
			'location': {'parent-uid': page_uid, 'order': 0},
			'block': {'string': parent_text}
		}
		create_block_status = create_block(client, create_block_body)
		if create_block_status == 200:
			parent_uid = q(client, query)
		else:
			logging.error(f"Failed to create parent block '{parent_text}'. Status code: {create_block_status}")
			return None

	return parent_uid

def add_block(client, parent_uid, block_text, order):
	create_block_body = {
		'action': 'create-block',
		'location': {'parent-uid': parent_uid, 'order': 0 if order == 'first' else -1},
		'block': {'string': block_text}
	}
	create_block_status = create_block(client, create_block_body)
	if create_block_status != 200:
		logging.error(f"Failed to add block. Status code: {create_block_status}")
		return False
	return True

def main():
	parser = argparse.ArgumentParser(description="Add a block to a page in Roam Research.")
	parser.add_argument("blocktext", help="The text content of the block to add.")
	parser.add_argument("-pg", "--page", help="The page to add the block to. Can be a date (YYYY-MM-DD), a page title, or a page UID. If not provided, defaults to today's daily page.")
	parser.add_argument("-pb", "--parent", help="The text of the parent block under which to nest the new block. If not found, it will be created.")
	parser.add_argument("-o", "--order", default="last", choices=["first", "last"], help="Where to add the block (default: last)")

	args = parser.parse_args()

	# Initialize RoamBackendClient
	client = initialize_graph({'token': os.getenv('ROAM_API_TOKEN'), 'graph': os.getenv('ROAM_GRAPH_NAME')})

	# Process the page argument
	if not args.page:
		args.page = datetime.now().strftime("%Y-%m-%d")

	# Get or create the page UID
	page_uid = get_or_create_page_uid(client, args.page)
	if not page_uid:
		logging.error(f"Could not find or create page: {args.page}")
		sys.exit(1)

	if args.parent:
		# Find or create the parent block
		parent_uid = find_or_create_parent_block(client, page_uid, args.parent)
		if parent_uid is None:
			logging.error(f"Could not find or create parent block: {args.parent}")
			sys.exit(1)
	else:
		parent_uid = page_uid

	# Add the block
	if add_block(client, parent_uid, args.blocktext, args.order):
		logging.info("Block added successfully")
	else:
		logging.error("Failed to add block")
		sys.exit(1)

if __name__ == "__main__":
	main()