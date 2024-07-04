#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Add Block to Roam Page - add_block.py
Description:  A script to add a block to a specified page or today's daily page in Roam Research, optionally as a child of a parent block.
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-04
Version:      2.4
License:      MIT
"""

import os
import sys
import argparse
import datetime
import re
from dotenv import load_dotenv
import logging

# Set up logging at the beginning of your script
logging.basicConfig(level=logging.ERROR)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI, get_roam_date_format, q

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def process_block_text(block_text):
	# Replace literal '\n' with actual newline characters
	block_text = block_text.replace('\\n', '\n')

	lines = block_text.split('\n')
	processed_lines = []
	for line in lines:
		if line.strip().startswith("[]"):
			processed_lines.append(line.replace("[]", "{{[[TODO]]}}"))
		elif line.strip().startswith("[x]"):
			processed_lines.append(line.replace("[x]", "{{[[DONE]]}}"))
		else:
			processed_lines.append(line)

	return '\n'.join(processed_lines)


def get_or_create_page_uid(roam, page):
	if page is None or page == "":
		# Default to today's daily page
		today = datetime.datetime.now()
		page_title = get_roam_date_format(today)
		return roam.get_or_create_daily_note(page_title)
	elif re.match(r'^\d{4}-\d{2}-\d{2}$', page):
		# It's a date in YYYY-MM-DD format
		try:
			date_obj = datetime.datetime.strptime(page, "%Y-%m-%d")
			page_title = get_roam_date_format(date_obj)
			return roam.get_or_create_daily_note(page_title)
		except ValueError:
			print("Error: Invalid date format. Please use YYYY-MM-DD.")
			return None
	elif re.match(r'^[a-zA-Z0-9]{9}$', page):
		# It looks like a UID
		return page
	else:
		# Treat it as a regular page title
		page_uid = roam.get_page_uid(page)
		if not page_uid:
			# If page doesn't exist, create it
			roam.create_page(page)
			page_uid = roam.get_page_uid(page)
		return page_uid

def find_or_create_parent_block(roam, page_uid, parent_text):
	# Search for the parent block
	query = f'[:find (pull ?b [:block/uid]) . :where [?b :block/page ?p] [?p :block/uid "{page_uid}"] [?b :block/string "{parent_text}"]]'
	result = q(roam.client, query)
	logging.debug(f"Query result: {result}")

	if result and ':block/uid' in result:
		parent_uid = result[':block/uid']
		logging.debug(f"Found existing parent block with UID: {parent_uid}")
		return parent_uid
	else:
		logging.debug(f"Parent block not found. Creating new parent block.")
		# If parent block doesn't exist, create it
		success = roam.add_block(page_uid, parent_text)
		if success:
			# We need to query for the UID of the block we just created
			new_query = f'[:find (pull ?b [:block/uid]) . :where [?b :block/page ?p] [?p :block/uid "{page_uid}"] [?b :block/string "{parent_text}"]]'
			new_result = q(roam.client, new_query)
			if new_result and ':block/uid' in new_result:
				parent_uid = new_result[':block/uid']
				logging.debug(f"Created new parent block with UID: {parent_uid}")
				return parent_uid
			else:
				logging.error(f"Failed to retrieve UID of newly created parent block")
				return None
		else:
			logging.error(f"Failed to create new parent block")
			return None



def add_block_to_page(page, block_text, parent=None, order='last'):
	if not block_text.strip():
		print("Error: Block text cannot be empty.")
		return

	# Initialize RoamAPI
	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

	# Process the block text
	processed_block_text = process_block_text(block_text)
	block_lines = processed_block_text.split('\n')

	# Get or create the page UID
	page_uid = get_or_create_page_uid(roam, page)
	logging.debug(f"Page UID: {page_uid}")

	if not page_uid:
		print(f"Error: Could not find or create page: {page}")
		return

	if parent:
		# Find or create the parent block
		parent_uid = find_or_create_parent_block(roam, page_uid, parent)
		logging.debug(f"Parent UID: {parent_uid}")
		if parent_uid is None:
			print(f"Error: Could not find or create parent block: {parent}")
			return
		# Add the new blocks as children of the parent block
		success = True
		for line in block_lines:
			logging.debug(f"Attempting to add block: {line} under parent: {parent_uid}")
			success = success and roam.add_block(parent_uid, line, order)
	else:
		# Add the new blocks to the page
		success = True
		for line in block_lines:
			logging.debug(f"Attempting to add block: {line} to page: {page_uid}")
			success = success and roam.add_block(page_uid, line, order)

	if success:
		print(f"Successfully added new block(s) to the page")
	else:
		print(f"Failed to add block(s) to the page")

	logging.debug(f"Add block result: {success}")



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Add a block to a page in Roam Research.")
	parser.add_argument("--page", help="The page to add the block to. Can be a date (YYYY-MM-DD), a page title, or a page UID. If not provided, defaults to today's daily page.")
	parser.add_argument("--block", required=True, help="The text content of the block to add.")
	parser.add_argument("--parent", help="The text of the parent block under which to nest the new block. If not found, it will be created.")
	parser.add_argument("--order", default="last", choices=["first", "last"], help="Where to add the block (default: last)")

	args = parser.parse_args()

	add_block_to_page(args.page, args.block, args.parent, args.order)