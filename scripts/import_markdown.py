import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')

def process_markdown_file(file_path):
	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)
	success, title = roam.add_markdown_to_roam(file_path)

	if success:
		logging.info(f"Successfully added markdown content to page: {title}")
	else:
		logging.error(f"Failed to add markdown content to page: {title}")

if __name__ == "__main__":
	if len(sys.argv) != 2:
		logging.error("Usage: python process_markdown.py <markdown_file>")
		sys.exit(1)

	markdown_file = sys.argv[1]
	process_markdown_file(markdown_file)