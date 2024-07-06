#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title:        link-roam.py
Description:  Link Roam Research page to DevonThink 3 and log it.
Author:       Ian Shen
Date:         2024-07-06
Version:      1.2.3
License:      MIT
"""

import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from roam_api_utils import RoamAPI

__version__ = "1.2.4"

def process_roam_link(page_title, dt_schema_url=None):
    load_dotenv()
    roam = RoamAPI(os.getenv('ROAM_GRAPH_NAME'), os.getenv('ROAM_API_TOKEN'))

    try:
        daily_page_uid = roam.get_or_create_daily_note(datetime.now())
        if not daily_page_uid:
            raise Exception("Failed to create or retrieve daily page")

        log_block_uid = roam.find_or_create_parent_block(daily_page_uid, "[[Log/DevonThink]]")
        if not log_block_uid:
            raise Exception("Failed to create or find Log/DevonThink block")

        if dt_schema_url:
            link_block_uid = roam.add_block_with_retry(log_block_uid, f"Linked [[{page_title}]] to [DT3—{page_title}]({dt_schema_url})")
            if not link_block_uid:
                raise Exception("Failed to add link block")

        # Get the UID of Page page_title
        page_uid = roam.get_or_create_page_uid(page_title)
        if not page_uid:
            raise Exception(f"Failed to create or retrieve page: {page_title}")

        roam_link = f"https://roamresearch.com/#/app/{os.getenv('ROAM_GRAPH_NAME')}/page/{page_uid}"

        return {
            "status": "success",
            "result": {
                "roam_url": roam_link,
                "dt_url": dt_schema_url if dt_schema_url else None
            }
        }
    except Exception as e:
        return {"status": "error", "result": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Link Roam Research page to DevonThink 3 and log it.")
    parser.add_argument("page_title", help="Roam Research page title; Will create if not found.")
    parser.add_argument("-dt", "--devonthink", help="DevonThink 3 schema URL", required=True)
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    result = process_roam_link(args.page_title, args.devonthink)
    print(json.dumps(result, indent=2))