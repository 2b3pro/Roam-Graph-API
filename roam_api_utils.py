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
import json
import yaml
from client import initialize_graph, create_block, q
import logging

# Set up logging at the beginning of your script
logging.basicConfig(
	level=logging.DEBUG,
	format='%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]')

def get_roam_date_format(date):
	"""Convert a date to the format Roam uses for daily pages."""
	if isinstance(date, str):
		# If it's already a string, assume it's in the correct format and return it
		return date

	suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
	day = date.day
	suffix = suffixes.get(day % 10, 'th') if day not in [11, 12, 13] else 'th'
	return date.strftime(f"%B {day}{suffix}, %Y")

def parse_markdown(content):
	lines = content.split('\n')
	blocks = []
	stack = [{'level': 0, 'children': blocks}]

	for line in lines:
		stripped = line.strip()
		if not stripped:
			continue

		indent = len(line) - len(line.lstrip())

		if line.startswith('#'):
			# Handle headings
			level = len(line.split()[0])
			new_block = {'content': stripped[level:].strip(), 'properties': {'heading': level}, 'children': []}
			while stack[-1]['level'] >= level:
				stack.pop()
			stack[-1]['children'].append(new_block)
			stack.append({'level': level, 'children': new_block['children']})
		elif line.startswith('- '):
			# Handle bullet points
			content = stripped[2:].strip()
			new_block = {'content': content, 'properties': {'bullet': True}, 'children': []}
			while stack[-1]['level'] >= indent:
				stack.pop()
			stack[-1]['children'].append(new_block)
			stack.append({'level': indent, 'children': new_block['children']})
		elif re.match(r'^\d+\.', stripped):
			# Handle numbered lists
			content = re.sub(r'^\d+\.\s*', '', stripped)
			new_block = {'content': content, 'properties': {'numbered': True}, 'children': []}
			while stack[-1]['level'] >= indent:
				stack.pop()
			stack[-1]['children'].append(new_block)
			stack.append({'level': indent, 'children': new_block['children']})
		else:
			# Regular content
			new_block = {'content': stripped, 'children': []}
			while stack[-1]['level'] >= indent:
				stack.pop()
			stack[-1]['children'].append(new_block)

	return blocks

def process_block_text(block_text):
	# Replace literal '\n' with actual newline characters
	block_text = block_text.replace('\\n', '\n')

	lines = block_text.split('\n')
	processed_lines = []

	# Replaces TODO/DONE codes
	for line in lines:
		if line.strip().startswith("[]"):
			processed_lines.append(line.replace("[]", "{{[[TODO]]}}"))
		elif line.strip().startswith("[x]"):
			processed_lines.append(line.replace("[x]", "{{[[DONE]]}}"))
		else:
			processed_lines.append(line)

	return '\n'.join(processed_lines)

class RoamAPI:
	def __init__(self, graph, token):
		self.client = initialize_graph({"graph": graph, "token": token})
		self.__uid_cache = {}
		self.__last_request_time = 0
		self.__min_request_interval = 0.1  # 100ms between requests


	# Page-Related Definitions ----------------------------------------

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

	def get_or_create_page_uid(self, page):
		if page in self.__uid_cache:
			return self.__uid_cache[page]

		if page is None or page == "":
			# Default to today's daily page
			today = datetime.datetime.now()
			page_title = get_roam_date_format(today)
			uid = self.get_or_create_daily_note(page_title)
		elif re.match(r'^\d{4}-\d{2}-\d{2}$', page):
			# It's a date in YYYY-MM-DD format
			try:
				date_obj = datetime.datetime.strptime(page, "%Y-%m-%d")
				page_title = get_roam_date_format(date_obj)
				uid = self.get_or_create_daily_note(page_title)
			except ValueError:
				print("Error: Invalid date format. Please use YYYY-MM-DD.")
				return None
		elif re.match(r'^[a-zA-Z0-9]{9}$', page):
			# It looks like a UID
			uid = page
		else:
			# Treat it as a regular page title
			uid = self.get_page_uid(page)
			if not uid:
				# If page doesn't exist, create it
				self.create_page(page)
				uid = self.get_page_uid(page)

		if uid:
			self.__uid_cache[page] = uid
		return uid

	def create_block_with_children(self, parent_uid, block):
		content = block.get('content', '')
		logging.debug(f"Processing block: {block}")
		if isinstance(content, str) and content.strip():
			block_data = {
				"location": {"parent-uid": parent_uid, "order": "last"},
				"block": {"string": content.strip()}
			}
			properties = block.get('properties', {})
			if properties:
				block_data["block"].update(properties)

			logging.debug(f"Block data: {json.dumps(block_data, indent=2)}")

			result = self._make_api_call(create_block, self.client, block_data)
			if result is None:
				logging.error(f"Failed to create block: {content[:50]}...")
				return

			new_block_uid = self.get_last_block_uid(parent_uid)
			if new_block_uid:
				# Create child blocks
				for child in block.get('children', []):
					self.create_block_with_children(new_block_uid, child)

			time.sleep(self.__min_request_interval)
		else:
			logging.warning(f"Skipping invalid block: {block}")

	def batch_create_blocks(self, parent_uid, blocks):
		logging.info(f"Starting batch_create_blocks with {len(blocks)} top-level blocks")
		for block in blocks:
			result = self.create_block_with_children(parent_uid, block)
			if result is None:
				logging.warning("Failed to create block, pausing import...")
				time.sleep(60)  # Pause for a minute before continuing
			else:
				time.sleep(2)  # Add a 2-second delay between top-level blocks

	def _make_api_call(self, func, *args, **kwargs):
		max_retries = 10
		initial_delay = 60  # Increased from 30 to 60 seconds
		max_delay = 300  # Maximum delay of 5 minutes
		consecutive_rate_limits = 0
		max_consecutive_rate_limits = 5

		for attempt in range(max_retries):
			try:
				result = func(*args, **kwargs)
				self.__last_request_time = time.time()
				logging.debug(f"Successful API call: {func.__name__}")
				return result
			except Exception as e:
				if "Error (HTTP 503)" in str(e):
					consecutive_rate_limits += 1
					if consecutive_rate_limits > max_consecutive_rate_limits:
						logging.error(f"Hit rate limit {max_consecutive_rate_limits} times in a row. Aborting.")
						return None

					delay = min(initial_delay * (2 ** attempt) + random.uniform(0, 10), max_delay)
					logging.warning(f"Rate limit hit. Waiting for {delay:.2f} seconds before retrying...")
					time.sleep(delay)
				else:
					logging.error(f"Error in API call: {str(e)}")
					logging.error(f"Function: {func.__name__}, Args: {args}, Kwargs: {kwargs}")
					return None

		logging.error("Max retries reached. Failed to make API call.")
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

	# Block-related Definitions --------------------------------------

	def _add_blocks(self, parent_uid, blocks):
		last_heading_uid = None
		for block in blocks:
			content = block.pop('content')
			properties = block.copy()

			# Check if this is a numbered list item following a heading
			if last_heading_uid and re.match(r'^\d+\.', content):
				parent_uid = last_heading_uid  # Indent under the last heading

			new_block_uid = self.add_block(parent_uid, content, **properties)

			if new_block_uid:
				if 'heading' in properties:
					last_heading_uid = new_block_uid
				if 'children' in block:
					self._add_blocks(new_block_uid, block['children'])

			time.sleep(0.5)  # Add a 0.5 second delay between adding blocks

	def add_block_with_retry(self, parent_uid, content, **properties):
		max_retries = 10  # Increased to allow for more retries
		initial_delay = 30  # Wait 30 seconds after first rate limit hit
		retry_interval = 5  # Try every 5 seconds thereafter

		for attempt in range(max_retries):
			try:
				block_data = {
					"location": {"parent-uid": parent_uid, "order": "last"},
					"block": {"string": content}
				}
				if properties:
					block_data["block"].update(properties)

				status_code = create_block(self.client, block_data)
				if status_code == 200:
					return self.get_last_block_uid(parent_uid)
				else:
					print(f"Unexpected status code {status_code} on attempt {attempt + 1}")
			except Exception as e:
				if "Error (HTTP 503)" in str(e):
					if attempt == 0:
						print(f"Rate limit hit. Waiting for {initial_delay} seconds before retrying...")
						time.sleep(initial_delay)
					else:
						print(f"Rate limit still in effect. Retrying in {retry_interval} seconds...")
						time.sleep(retry_interval)
				else:
					print(f"Error adding block: {str(e)}")
					return None

		print("Max retries reached. Failed to add block.")
		return None

	def add_block_to_page(self, block_text, page=None, parent=None, order='last'):
		if not block_text.strip():
			print("Error: Block text cannot be empty.")
			return

		# Process the block text
		processed_block_text = process_block_text(block_text)
		block_lines = processed_block_text.split('\n')

		# Get or create the page UID
		page_uid = self.get_or_create_page_uid(page)
		if not page_uid:
			print(f"Error: Could not find or create page: {page}")
			return

		if parent:
			# Find or create the parent block
			parent_uid = self.find_or_create_parent_block(page_uid, parent)
			if parent_uid is None:
				print(f"Error: Could not find or create parent block: {parent}")
				return
			# Add the new blocks as children of the parent block
			success = True
			for line in block_lines:
				success = success and self.add_block_with_retry(parent_uid, line, order=order)
		else:
			# Add the new blocks to the page
			success = True
			for line in block_lines:
				success = success and self.add_block_with_retry(page_uid, line, order=order)

		if success:
			print(f"Successfully added new block(s) to the page")
		else:
			print(f"Failed to add block(s) to the page")

	def get_last_block_uid(self, parent_uid):
		max_retries = 10
		initial_delay = 30
		retry_interval = 5

		for attempt in range(max_retries):
			try:
				query = f"""
					[:find ?uid .
					 :where
					 [?p :block/uid "{parent_uid}"]
					 [?p :block/children ?c]
					 [?c :block/uid ?uid]
					 (not-join [?c]
					   [?p :block/children ?c2]
					   [?c2 :create/time ?t2]
					   [?c :create/time ?t]
					   [(> ?t2 ?t)])]
				"""
				result = q(self.client, query)
				if result:
					return result
				else:
					print(f"No result found on attempt {attempt + 1}")
					time.sleep(retry_interval)  # Wait before retrying if no result
			except Exception as e:
				if "Error (HTTP 503)" in str(e):
					if attempt == 0:
						print(f"Rate limit hit. Waiting for {initial_delay} seconds before retrying...")
						time.sleep(initial_delay)
					else:
						print(f"Rate limit still in effect. Retrying in {retry_interval} seconds...")
						time.sleep(retry_interval)
				else:
					print(f"Error getting last block UID: {str(e)}")
					time.sleep(retry_interval)  # Wait before retrying on other errors

		print("Max retries reached. Failed to get last block UID.")
		return None

# 	def add_nested_blocks(self, parent_uid, blocks, order='last'):
# 		"""
# 		Add nested blocks to a page or another block.
#
# 		:param parent_uid: UID of the parent page or block
# 		:param blocks: List of dictionaries, each containing 'string' and optional 'children'
# 		:param order: Where to add the blocks ('first', 'last', or a number)
# 		:return: Boolean indicating success
# 		"""
# 		try:
# 			for block in blocks:
# 				# Create the main block
# 				success = self.add_block(parent_uid, block['string'], order)
# 				if not success:
# 					return False
#
# 				# Get the UID of the newly created block
# 				new_block_uid = self.get_last_block_uid(parent_uid)
#
# 				# If this block has children, recursively add them
# 				if 'children' in block and block['children']:
# 					if not self.add_nested_blocks(new_block_uid, block['children']):
# 						return False
#
# 			return True
# 		except Exception as e:
# 			print(f"Error adding nested blocks: {str(e)}")
# 			return False

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

	def find_or_create_parent_block(self, page_uid, parent_text):
		# Search for the parent block
		query = f'[:find (pull ?b [:block/uid]) . :where [?b :block/page ?p] [?p :block/uid "{page_uid}"] [?b :block/string "{parent_text}"]]'
		result = q(self.client, query)
		logging.debug(f"Query result: {result}")

		if result and ':block/uid' in result:
			parent_uid = result[':block/uid']
			logging.debug(f"Found existing parent block with UID: {parent_uid}")
			return parent_uid
		else:
			logging.debug(f"Parent block not found. Creating new parent block.")
			# If parent block doesn't exist, create it
			success = self.add_block(page_uid, parent_text)
			if success:
				# We need to query for the UID of the block we just created
				new_query = f'[:find (pull ?b [:block/uid]) . :where [?b :block/page ?p] [?p :block/uid "{page_uid}"] [?b :block/string "{parent_text}"]]'
				new_result = q(self.client, new_query)
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

	# Other Definitions ---------------------------------------------

	def get_graph_structure(self):
		"""Get a high-level structure of the graph (pages and their immediate children)."""
		query = '[:find (pull ?e [:node/title {:block/children [:block/string]}]) :where [?e :node/title]]'
		return q(self.client, query)

	def get_page(self, query, prefix, output_format='json'):
		logging.info(f"Line 370: Prefix is equal to {prefix}")

		today = datetime.datetime.now()
		if query == "today":
			# Default to today's daily page
			query = get_roam_date_format(today)
		elif query == "yesterday":
			yesterday = today - datetime.timedelta(days=1)
			query = get_roam_date_format(yesterday)
		elif query == "lastweek":
			lastweek = today - datetime.timedelta(days=7)
			query = get_roam_date_format(lastweek)
		elif re.match(r'^\d{4}-\d{2}-\d{2}$', query):
			# It's a date in YYYY-MM-DD format
			date_obj = datetime.datetime.strptime(query, "%Y-%m-%d")
			query = get_roam_date_format(date_obj)

		# Search for the page
		page_uid = self.get_page_uid(query)

		if not page_uid:
			return f"No page found with title: {query}"

		# Get page content
		page_content = self.get_page_content(page_uid)

		if not page_content:
			return f"No content found for page: {query}"

		if output_format == 'json':
			return json.dumps(page_content, indent=2)
		elif output_format == 'markdown':
			if prefix is not None and prefix != "":
				prefix = f"{prefix} " # adds a space after
			elif prefix is None:
				prefix = ""
			logging.info(f"Line 406: Prefix is equal to {prefix}")
			return convert_to_markdown(page_content, prefix)
		else:
			raise ValueError("Invalid output format. Use 'json' or 'markdown'.")

	def import_markdown_file(self, file_path):
		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				content = file.read()

			parts = content.split('---', 2)
			if len(parts) < 3:
				return False, "No valid YAML frontmatter found in the file"

			metadata = yaml.safe_load(parts[1])
			title = metadata.get('title')
			if not title:
				return False, "No title found in YAML frontmatter"

			page_uid = self.get_or_create_page_uid(title)
			if not page_uid:
				return False, f"Failed to create page: {title}"

			blocks = parse_markdown(parts[2].strip())
			self.batch_create_blocks(page_uid, blocks)

			return True, f"Successfully imported to page: {title}"
		except Exception as e:
			return False, f"Error importing file: {str(e)}"

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