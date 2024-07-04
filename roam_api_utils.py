#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        roam_api_utils.py
Description:  A set of python utilites to interact with Roam Research graphs.
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-04
Version:      1.2
License:      MIT
"""

import time
import datetime
import re
from client import initialize_graph, create_block, q

def get_roam_date_format(date):
	"""Convert a date to the format Roam uses for daily pages."""
	suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
	day = date.day
	suffix = suffixes.get(day % 10, 'th') if day not in [11, 12, 13] else 'th'
	return date.strftime(f"%B {day}{suffix}, %Y")

def parse_markdown(file_path):
	"""Parse a markdown file into a nested block structure."""
	with open(file_path, 'r') as file:
		content = file.read()

	lines = content.split('\n')
	title = lines[0].strip('# ')
	blocks = []
	stack = [(0, blocks)]

	for line in lines[1:]:
		if line.strip() == '':
			continue

		match = re.match(r'^(\t*)- (.*)', line)
		if match:
			indent = len(match.group(1))
			content = match.group(2)

			while stack and stack[-1][0] >= indent:
				stack.pop()

			if not stack:
				# If stack is empty, reset to root level
				stack = [(0, blocks)]

			new_block = {'string': content}
			if stack[-1][0] < indent:
				parent = stack[-1][1][-1] if stack[-1][1] else {'children': []}
				parent.setdefault('children', []).append(new_block)
				stack.append((indent, parent['children']))
			else:
				stack[-1][1].append(new_block)

	return title, blocks

class RoamAPI:
	def __init__(self, graph, token):
		self.client = initialize_graph({"graph": graph, "token": token})


	def create_page(self, title):
		"""Create a new page with the given title."""
		try:
			create_block(self.client, {
				"location": {"page-title": title, "order": 0},
				"block": {"string": title}
			})
			return title
		except Exception as e:
			print(f"Error creating page: {str(e)}")
			return None

	def get_or_create_daily_note(self, date=None):
		"""Get or create a daily note for the given date (or today if not specified)."""
		if date is None:
			date = datetime.datetime.now()
		date_string = get_roam_date_format(date)

		# Check if the page already exists
		page_uid = self.get_page_uid(date_string)

		if not page_uid:
			# If the page doesn't exist, create it
			self.create_page(date_string)
			page_uid = self.get_page_uid(date_string)

		return page_uid

	def add_block(self, parent_uid, content, order='last'):
			"""Add a block to a page or another block using its UID."""
			try:
				create_block(self.client, {
					"location": {"parent-uid": parent_uid, "order": order},
					"block": {"string": content}
				})
				return True
			except Exception as e:
				print(f"Error adding block: {str(e)}")
				return False

	def get_last_block_uid(self, parent_uid):
		"""Get the UID of the last block added to a page or block."""
		query = f'[:find ?uid . :where [?e :block/uid "{parent_uid}"] [?e :block/children ?c] [?c :block/uid ?uid] (not-join [?c] [?c :block/children _])]'
		return q(self.client, query)

	def add_nested_blocks(self, parent_uid, blocks, order='last'):
		"""
		Add nested blocks to a page or another block.

		:param parent_uid: UID of the parent page or block
		:param blocks: List of dictionaries, each containing 'string' and optional 'children'
		:param order: Where to add the blocks ('first', 'last', or a number)
		:return: Boolean indicating success
		"""
		try:
			for block in blocks:
				# Create the main block
				success = self.add_block(parent_uid, block['string'], order)
				if not success:
					return False

				# Get the UID of the newly created block
				new_block_uid = self.get_last_block_uid(parent_uid)

				# If this block has children, recursively add them
				if 'children' in block and block['children']:
					if not self.add_nested_blocks(new_block_uid, block['children']):
						return False

			return True
		except Exception as e:
			print(f"Error adding nested blocks: {str(e)}")
			return False

	def add_markdown_to_roam(self, file_path):
			"""Process a markdown file and add its content to Roam."""
			try:
				title, blocks = parse_markdown(file_path)

				# Create the page
				self.create_page(title)
				page_uid = self.get_page_uid(title)

				if not page_uid:
					logging.error(f"Failed to create or retrieve page: {title}")
					return False, title

				# Add the blocks
				success = self.add_nested_blocks(page_uid, blocks)

				if not success:
					logging.error(f"Failed to add blocks to page: {title}")
					return False, title

				return True, title
			except Exception as e:
				logging.error(f"Error processing markdown file: {str(e)}")
				return False, ""
	def get_page_uid(self, page_title):
		"""Get the UID of a page by its title."""
		query = f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]'
		return q(self.client, query)

	def get_block_uids(self, page_title):
		"""Get the UIDs of all blocks on a page."""
		query = f'[:find [?uid ...] :where [?e :node/title "{page_title}"] [?e :block/children ?c] [?c :block/uid ?uid]]'
		return q(self.client, query)

	def get_block_content(self, block_uid):
		"""Get the content of a block by its UID."""
		query = f'[:find ?string . :where [?b :block/uid "{block_uid}"] [?b :block/string ?string]]'
		return q(self.client, query)

	def update_block(self, block_uid, new_content):
		"""Update the content of a block."""
		try:
			create_block(self.client, {
				"action": "update-block",
				"block": {
					"uid": block_uid,
					"string": new_content
				}
			})
			return True
		except Exception as e:
			print(f"Error updating block: {str(e)}")
			return False

	def delete_block(self, block_uid):
		"""Delete a block by its UID."""
		try:
			create_block(self.client, {
				"action": "delete-block",
				"block": {
					"uid": block_uid
				}
			})
			return True
		except Exception as e:
			print(f"Error deleting block: {str(e)}")
			return False

	def move_block(self, block_uid, new_parent_uid, new_order):
		"""Move a block to a new parent and/or position."""
		try:
			create_block(self.client, {
				"action": "move-block",
				"location": {
					"parent-uid": new_parent_uid,
					"order": new_order
				},
				"block": {
					"uid": block_uid
				}
			})
			return True
		except Exception as e:
			print(f"Error moving block: {str(e)}")
			return False

	def search_pages(self, search_string):
		"""Search for pages containing the given string."""
		query = f'[:find [?title ...] :where [?e :node/title ?title] [(clojure.string/includes? ?title "{search_string}")]]'
		return q(self.client, query)

	def get_page_references(self, page_title):
		"""Get all pages that reference the given page."""
		query = f'[:find [?ref_title ...] :where [?e :node/title "{page_title}"] [?ref :block/refs ?e] [?ref_page :block/children ?ref] [?ref_page :node/title ?ref_title]]'
		return q(self.client, query)

	def get_page_content(self, page_uid):
		query = f'''[
			:find (pull ?e [:node/title {{:block/children [:block/string :block/uid {{:block/children ...}}]}}])
			:where [?e :block/uid "{page_uid}"]
		]'''
		result = q(self.client, query)
		return result[0][0] if result else None

	def get_or_create_daily_note(self, date=None):
		"""Get or create a daily note for the given date (or today if not specified)."""
		if date is None:
			date = datetime.datetime.now()
		date_string = get_roam_date_format(date)

		# Check if the page already exists
		page_uid = self.get_page_uid(date_string)

		if not page_uid:
			# If the page doesn't exist, create it
			self.create_page(date_string)
			page_uid = self.get_page_uid(date_string)

		return page_uid

	def get_graph_structure(self):
		"""Get a high-level structure of the graph (pages and their immediate children)."""
		query = '[:find (pull ?e [:node/title {:block/children [:block/string]}]) :where [?e :node/title]]'
		return q(self.client, query)

# Example usage
if __name__ == "__main__":
	import os
	from dotenv import load_dotenv

	load_dotenv()
	ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
	ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

	# Example: Create a page and add some blocks
	page_title = "API Test Page " + time.strftime("%Y%m%d%H%M%S")
	roam.create_page(page_title)
	roam.add_block(page_title, "This is a test block")
	roam.add_block(page_title, "This is another test block")

	# Get and print page content
	page_uid = roam.get_page_uid(page_title)
	block_uids = roam.get_block_uids(page_title)
	print(f"Page UID: {page_uid}")
	print("Blocks:")
	for uid in block_uids:
		content = roam.get_block_content(uid)
		print(f"- {content}")

	print("Test completed.")