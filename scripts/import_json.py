import os
import sys
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

def add_json_to_roam(file_path):
	roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

	success = roam.import_json_file_to_page(file_path)

	if success:
		print(f"Successfully added JSON content to Roam")
	else:
		print(f"Failed to add JSON content to Roam")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Parse JSON file and add content to Roam Research.")
	parser.add_argument("json_file", help="Path to the JSON file to parse")

	args = parser.parse_args()

	add_json_to_roam(args.json_file)