import os
import time
from dotenv import load_dotenv
from client import initialize_graph, create_block, q

# Load environment variables from .env file
load_dotenv()

# Get Roam API token and graph name from environment variables
ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def main():
    # Initialize the Roam client
    client = initialize_graph({
        "graph": ROAM_GRAPH_NAME,
        "token": ROAM_API_TOKEN
    })

    # Create a new page
    page_title = "Hello World " + str(int(time.time()))
    print(f"Creating new page: {page_title}")
    try:
        create_block(client, {
            "location": {"page-title": page_title, "order": 0},
            "block": {"string": page_title}
        })
        print("Page created successfully")
    except Exception as e:
        print(f"Error creating page: {str(e)}")
        return

    # Add a block to the new page
    print("Adding a block to the page...")
    try:
        create_block(client, {
            "location": {"page-title": page_title, "order": 1},
            "block": {"string": "Hello, Roam Research API!"}
        })
        print("Block added successfully")
    except Exception as e:
        print(f"Error adding block: {str(e)}")
        return

    # Wait for a moment to ensure changes are processed
    time.sleep(2)

    # Retrieve and display page content
    print("\nRetrieving page content:")
    try:
        # Get page UID
        query = f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]'
        page_uid = q(client, query)
        print(f"Page UID: {page_uid}")

        # Get block UIDs
        query = f'[:find [?uid ...] :where [?e :node/title "{page_title}"] [?e :block/children ?c] [?c :block/uid ?uid]]'
        block_uids = q(client, query)
        print(f"Block UIDs: {block_uids}")

        # Get block content
        print("Page content:")
        for uid in block_uids:
            query = f'[:find ?string . :where [?b :block/uid "{uid}"] [?b :block/string ?string]]'
            block_content = q(client, query)
            print(f"- {block_content}")

    except Exception as e:
        print(f"Error retrieving page content: {str(e)}")

if __name__ == "__main__":
    main()