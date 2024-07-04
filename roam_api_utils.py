import time
from client import initialize_graph, create_block, q

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

	def add_block(self, page_title, content, order=None):
		"""Add a block to a page. If order is None, it will be added at the end."""
		try:
			location = {"page-title": page_title}
			if order is not None:
				location["order"] = order
			create_block(self.client, {
				"location": location,
				"block": {"string": content}
			})
			return True
		except Exception as e:
			print(f"Error adding block: {str(e)}")
			return False

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

	def create_daily_note(self, date_string=None):
		"""Create a daily note for the given date (or today if not specified)."""
		if date_string is None:
			date_string = time.strftime("%m-%d-%Y")
		return self.create_page(date_string)

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