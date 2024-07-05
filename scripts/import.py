#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Import JSON or Markdown file into Roam graph - import.py
Description:  This script will import a markdown file into Roam. JSON files will be reformatted accordingly.
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-05
Version:      1.1.0
License:      MIT
"""

import os
import sys
import yaml
import json
import argparse
from dotenv import load_dotenv
import logging

# Set up logging at the beginning of your script
logging.basicConfig(
	level=logging.ERROR,
	format='%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]')

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roam_api_utils import RoamAPI

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

ROAM_API_TOKEN = os.getenv('ROAM_API_TOKEN')
ROAM_GRAPH_NAME = os.getenv('ROAM_GRAPH_NAME')
roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

def parse_yaml_frontmatter(file_path):
	with open(file_path, 'r') as file:
		content = file.read()

	# Split the content into frontmatter and main content
	parts = content.split('---', 2)

	if len(parts) < 3:
		return None  # No valid frontmatter found

	frontmatter = parts[1].strip()
	# logging.debug(f"{frontmatter}")

	# Parse the YAML frontmatter
	try:
		yaml_data = yaml.safe_load(frontmatter)
		return yaml_data, content
	except yaml.YAMLError as e:
		print(f"Error parsing YAML frontmatter: {e}")
		return None

def import_json_file(file_path):
	try:
		with open(file_path, 'r') as file:
			json_data = json.load(file)

		# Generate markdown content
		markdown_content = "---\n"

		# Add metadata
		metadata = json_data.get("metadata", {})
		for key, value in metadata.items():
			if key == "tags":
				markdown_content += f"{key}: {' '.join(['#' + tag for tag in value])}\n"
			elif key == "featuredLinks":
				for link in value:
					markdown_content += f"  title: {link['title']}\n"
					markdown_content += f"  url: {link['url']}\n"
			else:
				markdown_content += f"{key}: {value}\n"

		markdown_content += "---\n"

		# Add page blocks
		def format_blocks(blocks, level=0):
			formatted = ""
			for block in blocks:
				formatted += f"{'  ' * level}- {block['block_text']}\n"
				if 'block_children' in block:
					formatted += format_blocks(block['block_children'], level + 1)
			return formatted

		markdown_content += format_blocks(json_data.get("page_blocks", []))

		# Write to a new markdown file
		output_file_path = os.path.splitext(file_path)[0] + '-tmp.md'
		with open(output_file_path, 'w') as output_file:
			output_file.write(markdown_content)

		print(f"Successfully converted JSON to Markdown: {output_file_path}")

		# Now import the generated markdown file
		import_markdown_file(output_file_path)

	except Exception as e:
		print(f"Error importing JSON file: {e}")

def remove_blank_lines(content):
	return '\n'.join(line for line in content.splitlines() if line.strip())

def import_markdown_file(file_path):
	try:
		success, message = roam.import_markdown_file(file_path)

		if success:
			print(message)
		else:
			print(f"Failed to import Markdown file: {message}")
	except Exception as e:
		print(f"Error importing Markdown file: {e}")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Import a file into a Roam graph.")
	parser.add_argument("file_path", help="Path to the file to parse {json, markdown, pdf}")

	args = parser.parse_args()

	file_extension = os.path.splitext(args.file_path)[1].lower()

	if file_extension == '.json':
		import_json_file(args.file_path)
	elif file_extension in ['.md', '.markdown']:
		import_markdown_file(args.file_path)
	elif file_extension == '.txt':
		# Assume it's markdown for now
		import_markdown_file(args.file_path)
	else:
		print(f"Unsupported file type: {file_extension}")