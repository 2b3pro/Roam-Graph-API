import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def search_roam(query, output_format='json'):
	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

	# Search for the page
	page_uid = roam.get_page_uid(query)

	if not page_uid:
		return f"No page found with title: {query}"

	# Get page content
	page_content = roam.get_page_content(page_uid)

	if not page_content:
		return f"No content found for page: {query}"

	if output_format == 'json':
		return json.dumps(page_content, indent=2)
	elif output_format == 'markdown':
		return convert_to_markdown(page_content)
	else:
		raise ValueError("Invalid output format. Use 'json' or 'markdown'.")

def convert_to_markdown(content, level=0):
	markdown = ""
	if level == 0 and ':node/title' in content:
		markdown += f"# {content[':node/title']}\n\n"
	for child in content.get(':block/children', []):
		markdown += "  " * level + "- " + child.get(':block/string', '') + "\n"
		if ':block/children' in child:
			markdown += convert_to_markdown({':block/children': child[':block/children']}, level + 1)
	return markdown

def write_to_file(content, filename):
	with open(filename, 'w', encoding='utf-8') as f:
		f.write(content)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Search Roam Research graph and return results.")
	parser.add_argument("query", help="The page title to search for")
	parser.add_argument("--format", choices=['json', 'markdown'], default='json', help="Output format (default: json)")
	parser.add_argument("--output-file", help="Output file path (if not provided, prints to stdout)")

	args = parser.parse_args()

	result = search_roam(args.query, args.format)
	if result:
		if args.output_file:
			write_to_file(result, args.output_file)
			print(f"Output written to {args.output_file}")
		else:
			print(result)
	else:
		print("No results found.")