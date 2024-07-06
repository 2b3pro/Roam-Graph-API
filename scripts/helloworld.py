"""
Title: Roam Research API HelloWorld
Description: A script to create a new page titled "Hello World" and add a block saying "I've greeted you for the first time!".
Author: Ian Shen
Version: 1.1.3
"""

import os
import logging
import sys
from dotenv import load_dotenv
from client import initialize_graph, create_page, create_block, q

# Load environment variables
load_dotenv()

# Set up logging with line numbers
logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(levelname)s - %(message)s at Line %(lineno)d')

def main():
	# Initialize the RoamBackendClient
	token = os.getenv('ROAM_API_TOKEN')
	graph = os.getenv('ROAM_GRAPH_NAME')

	if not token or not graph:
		logging.error("ROAM_API_TOKEN or ROAM_GRAPH_NAME environment variables are not set.")
		return

	try:
		client = initialize_graph({'token': token, 'graph': graph})

		# Create a new page titled "Hello World"
		page_title = "Hello World"
		create_page_body = {
			'action': 'create-page',
			'page': {
				'title': page_title
			}
		}
		logging.debug(f"Creating page with body: {create_page_body}")
		create_page_status = create_page(client, create_page_body)
		logging.debug(f"Create page status: {create_page_status}")

		if create_page_status == 200:
			logging.info(f'Page "{page_title}" created successfully.')

			# Query for the UID of the newly created page
			query = '[:find ?uid . :where [?e :node/title "Hello World"] [?e :block/uid ?uid]]'
			logging.debug(f"Querying for page UID with query: {query}")
			page_uid = q(client, query)
			logging.debug(f"Query result (page UID): {page_uid}")

			if page_uid:
				# Add a block to the new page
				block_content = "I've greeted you for the first time!"
				create_block_body = {
					'action': 'create-block',
					'location': {'parent-uid': page_uid, 'order': 0},
					'block': {'string': block_content}
				}
				logging.debug(f"Creating block with body: {create_block_body}")
				create_block_status = create_block(client, create_block_body)
				logging.debug(f"Create block status: {create_block_status}")

				if create_block_status == 200:
					logging.info(f'Block added to page "{page_title}" with content: "{block_content}"')
				else:
					logging.error(f'Failed to add block to page "{page_title}". Status code: {create_block_status}')
			else:
				logging.error(f'Failed to retrieve UID for page "{page_title}"')
		else:
			logging.error(f'Failed to create page "{page_title}". Status code: {create_page_status}')

	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		logging.error(f"An error occurred: {str(e)} at Line {exc_tb.tb_lineno}")

if __name__ == '__main__':
	main()