#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        Retrieves the requested page from Roam Research graph and return results - search.py
Description:  A script to search Roam graph
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-05
Version:      1.0
License:      MIT
"""

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
roam = RoamAPI(ROAM_GRAPH_NAME, ROAM_API_TOKEN)

def write_to_file(content, filename):
	with open(filename, 'w', encoding='utf-8') as f:
		f.write(content)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Retrieves the requested page from Roam Research graph and return results.", epilog="")
	parser.add_argument("query", help="The page title to search for, or a relative date {today, yesterday, lastweek} or an actual date YYYY-MM-DD.")
	parser.add_argument("-f","--format", choices=['json', 'markdown'], default='json', help="Output format (default: json)")
	parser.add_argument("-p","--prefix", help="Add a prefix before each line.")
	parser.add_argument("-o","--output", help="Output file path (defaults to stdout)")

	args = parser.parse_args()

	result = roam.get_page(args.query, args.prefix, args.format)
	if result:
		if args.output_file:
			write_to_file(result, args.output_file)
			print(f"Output written to {args.output_file}")
		else:
			print(result)
	else:
		print("No results found.")