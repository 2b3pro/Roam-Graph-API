import logging
from datetime import datetime
import time
import json
import os
import argparse
from dotenv import load_dotenv
from roamClient import initialize_graph, q, create_page, create_block
from roam_utils import get_roam_date_format

load_dotenv()

logging.basicConfig(level=logging.ERROR, format='%(message)s at Line %(lineno)d')
logger = logging.getLogger(__name__)

token = os.getenv('ROAM_API_TOKEN')
graph = os.getenv('ROAM_GRAPH_NAME')

client = initialize_graph({'graph': graph, 'token': token})

# Linked [[Theories about knowledge]] to [DT—Theories about knowledge](x-devonthink-item://57A06952-0E5F-4D45-B98E-F30906DCCEAA)

# Use the utilities
# create_page(client, {'page': {'title': get_roam_date_format(datetime.now()) }})
# daily_page_uid = "07-07-2024"
# today = get_roam_date_format(datetime.now())
#
# log_block_uid = q(client, '[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string ?s] [(clojure.string/includes? ?s "57A06952-0E5F-4D45-B98E-F30906DCCEAA")]]')
# print(log_block_uid)
# for uid in log_block_uids:
# 	block_content = q(client, f'[:find ?string . :where [?e :block/uid "{uid}"] [?e :block/string ?string]]')
# 	print(f"Block {uid}: {block_content}")

# log_block_result = create_block(client, {
# 	'location': {'parent-uid': daily_page_uid, 'order': 0},
# 	'block': {'string': "[[Log/DEVONthink]]"}
# })
# print(f"Results from block creation: {log_block_result}")

def find_nested_block(client, page_identifier, parent_string, target_string):
	# Step 1: Determine if we're dealing with a page title or UID
	if page_identifier.startswith('('):  # Assuming UIDs are wrapped in parentheses
		page_uid = page_identifier.strip('()')
		page_title_result = q(client, f'[:find ?title :where [?e :block/uid "{page_uid}"] [?e :node/title ?title]]')
		page_title = page_title_result[0][0] if page_title_result else "Unknown"
	else:
		page_title = page_identifier
		page_uid_result = q(client, f'[:find ?uid :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
		if not page_uid_result:
			return f"Page '{page_title}' not found."
		page_uid = page_uid_result[0][0]

	# Step 2: Find all child blocks of the page
	child_blocks = q(client, f'[:find ?child_uid ?child_string :where [?page :block/uid "{page_uid}"] [?page :block/children ?child] [?child :block/uid ?child_uid] [?child :block/string ?child_string]]')

	# Step 3: Find the parent block
	parent_block = next((block for block in child_blocks if parent_string in block[1]), None)
	if not parent_block:
		return f"No block containing '{parent_string}' found on page '{page_title}' (UID: {page_uid})."

	parent_uid, parent_content = parent_block

	# Step 4: Find all child blocks of the parent block
	parent_child_blocks = q(client, f'[:find ?child_uid ?child_string :where [?parent :block/uid "{parent_uid}"] [?parent :block/children ?child] [?child :block/uid ?child_uid] [?child :block/string ?child_string]]')

	# Step 5: Find the target block
	target_block = next((block for block in parent_child_blocks if target_string in block[1]), None)
	if not target_block:
		return f"No block containing '{target_string}' found under the parent block on page '{page_title}' (UID: {page_uid})."

	target_uid, target_string = target_block

	return f"""
	Found target block on page '{page_title}' (UID: {page_uid}):
	Under parent block: {parent_content}
	Parent block UID: {parent_uid}
	Target block UID: {target_uid}
	Target block content: {target_string}
	"""

# Example usage
page_identifier = "(hVTUkcyRK)"  # Replace with actual page title or UID (e.g., "(abcdefghij)")
parent_string = "References::"  # Replace with the content you're looking for in the parent block
target_string = "57A06952-0E5F-4D45-B98E-F30906DCCEAA"  # Replace with your target string

result = find_nested_block(client, page_identifier, parent_string, target_string)
print(result)