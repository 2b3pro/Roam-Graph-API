import os
import time
from dotenv import load_dotenv
from client import initialize_graph, create_block, q

# Load environment variables from .env file
load_dotenv()

# Get Roam API token and graph name from environment variables
ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def create_page_and_block(client):
	print("Creating a new page and attempting to add a block...")

	# Step 1: Create a new page
	page_title = "API Test Page " + str(int(time.time()))
	try:
		create_block(client, {
			"location": {"page-title": page_title, "order": 0},
			"block": {"string": page_title}
		})
		print(f"Page '{page_title}' created successfully")
	except Exception as e:
		print(f"Error creating page: {str(e)}")
		return

	# Step 2: Create a block on the newly created page using page-title
	print("Attempting to create a block on the new page using page-title...")
	try:
		create_block(client, {
			"location": {"page-title": page_title, "order": 1},
			"block": {"string": "This is a test block"}
		})
		print("Block created successfully")
	except Exception as e:
		print(f"Error creating block: {str(e)}")

	# Wait for 5 seconds
	print("Waiting for 5 seconds...")
	time.sleep(5)

	# Step 3: Query for the page UID
	print("Querying for the page UID...")
	try:
		query = '[:find ?uid . :where [?e :node/title "{}"] [?e :block/uid ?uid]]'.format(page_title)
		page_uid = q(client, query)
		print(f"Page UID: {page_uid}")

		# Step 4: Query for block UIDs
		print("Querying for block UIDs...")
		query = '[:find [?uid ...] :where [?e :node/title "{}"] [?e :block/children ?c] [?c :block/uid ?uid]]'.format(page_title)
		block_uids = q(client, query)
		print(f"Block UIDs: {block_uids}")

		# Step 5: Query for block content
		print("Querying for block content...")
		for uid in block_uids:
			query = '[:find ?string . :where [?b :block/uid "{}"] [?b :block/string ?string]]'.format(uid)
			block_content = q(client, query)
			print(f"Block {uid}: {block_content}")

	except Exception as e:
		print(f"Error querying for blocks: {str(e)}")

def main():
	# Initialize the Roam client
	client = initialize_graph({
		"graph": ROAM_GRAPH_NAME,
		"token": ROAM_API_TOKEN
	})

	create_page_and_block(client)

	print("\nTest completed.")

if __name__ == "__main__":
	main()