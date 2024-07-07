# -*- coding: utf-8 -*-
"""
Title:        link_dt-roam.py
Description:  Script to link DEVONthink items to Roam Research pages
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-06
Version:      4.1.0
License:      MIT
"""

import logging
import time
import json
import os
import argparse
# import subprocess
from datetime import datetime
from dotenv import load_dotenv
from client import initialize_graph, q, create_page, create_block
from roam_utils import get_roam_date_format, process_block_text

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_q_result(result):
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    elif isinstance(result, str):
        return result
    else:
        return None

def link_roam(page_title, dt, dtl=None, db=None, dbl=None, link_type="log", c=None, sc=None):
    try:
        token = os.getenv('ROAM_API_TOKEN')
        graph = os.getenv('ROAM_GRAPH_NAME')

        if not token or not graph:
            raise ValueError("ROAM_API_TOKEN or ROAM_GRAPH_NAME not set in .env file")

        client = initialize_graph({'graph': graph, 'token': token})
        logger.debug("Roam client initialized")

        today = get_roam_date_format(datetime.now())

        daily_page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :node/title "{today}"]]'))
        if not daily_page_uid:
            logger.debug(f"Creating daily page for {today}")
            create_page(client, {'page': {'title': today}})

            for _ in range(5):
                time.sleep(1)
                daily_page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :node/title "{today}"]]'))
                if daily_page_uid:
                    break
            else:
                raise Exception("Failed to create daily page")

        # On daily page, always use "[[Log/DEVONthink]]" as the parent block
        daily_parent_block_content = "[[Log/DEVONthink]]"
        daily_log_block_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{daily_parent_block_content}"] [?e :block/page ?p] [?p :block/uid "{daily_page_uid}"]]'))
        if not daily_log_block_uid:
            status_code, response_text = create_block(client, {
                'location': {'parent-uid': daily_page_uid, 'order': 0},
                'block': {'string': daily_parent_block_content}
            })
            if status_code != 200:
                raise Exception(f"Failed to create {daily_parent_block_content} block. Status: {status_code}, Response: {response_text}")
            daily_log_block_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{daily_parent_block_content}"] [?e :block/page ?p] [?p :block/uid "{daily_page_uid}"]]'))
            if not daily_log_block_uid:
                raise Exception(f"Failed to retrieve UID of newly created {daily_parent_block_content} block")

        # Create block content
        block_content = f"[{dt}]({dtl}) ⨠ [[{page_title}]]"
        if db and dbl:
            block_content = f"[[{db}]({dbl})]—{block_content}"

        logger.debug(f"Adding block to daily page: {block_content}")
        status_code, response_text = create_block(client, {
            'location': {'parent-uid': daily_log_block_uid, 'order': 0},
            'block': {'string': block_content}
        })
        if status_code != 200:
            raise Exception(f"Failed to create link block on daily page. Status: {status_code}, Response: {response_text}")

        time.sleep(3)

        page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]'))
        if page_uid:
            logger.debug(f"Got UID for {page_title}: {page_uid}")

            # On the linked page, use "[[Log/DEVONthink]]" or "References::" based on link_type
            page_parent_block_content = "[[Log/DEVONthink]]" if link_type == "log" else "References::"
            page_log_block_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{page_parent_block_content}"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]'))
            if not page_log_block_uid:
                status_code, response_text = create_block(client, {
                    'location': {'parent-uid': page_uid, 'order': 0},
                    'block': {'string': page_parent_block_content}
                })
                if status_code != 200:
                    raise Exception(f"Failed to create {page_parent_block_content} block on linked page. Status: {status_code}, Response: {response_text}")
                page_log_block_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{page_parent_block_content}"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]'))
                if not page_log_block_uid:
                    raise Exception(f"Failed to retrieve UID of newly created {page_parent_block_content} block on linked page")

            # Create block content
            if db and dbl:
                block_content = f"[[{db}]({dbl})]—[{dt}]({dtl})"
            else :
                block_content = f"[{dt}]({dtl})"

            # Add comment to the block if provided
            if c:
                block_content = process_block_text(f"{block_content} {c}")

            logger.debug(f"Adding block to linked page: {block_content}")
            status_code, response_text = create_block(client, {
                'location': {'parent-uid': page_log_block_uid, 'order': 0},
                'block': {'string': block_content}
            })
            if status_code != 200:
                raise Exception(f"Failed to create link block on linked page. Status: {status_code}, Response: {response_text}")

            # TODO: Create a nested block under the newly created content
            if sc:
                # Retrieve UID of the newly created block on the linked page, handle multiple results
                new_block_uids = process_q_result(q(client, f'[:find ?uid :where [?e :block/uid ?uid] [?e :block/string "{block_content}"]]'))
                if not new_block_uids:
                    raise Exception("Failed to retrieve UID of the newly created block")

                if isinstance(new_block_uids, list) and len(new_block_uids) > 0:
                    new_block_uid = new_block_uids[0]  # Assuming the first UID is the correct one
                else:
                    new_block_uid = new_block_uids

                sc = process_block_text(sc)
                status_code, response_text = create_block(client, {
                    'location': {'parent-uid': new_block_uid, 'order': 0},
                    'block': {'string': sc}
                })
                if status_code != 200:
                    raise Exception(f"Failed to create nested block. Status: {status_code}, Response: {response_text}")

        else:
            logger.warning(f"UID not found for {page_title}")
            page_uid = ""

        roam_url = f"https://roamresearch.com/#/app/{graph}/page/{page_uid}"

        return json.dumps({
            "status": "success",
            "message": "Link created successfully",
            "dt_url": dt,
            "roam_url": roam_url
        })

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

def main():
    parser = argparse.ArgumentParser(description="Link DEVONthink page to Roam Research")
    parser.add_argument("page_title", help="The title of the page in Roam graph to be linked")
    parser.add_argument("-t", choices=["log", "ref"], default="log", help="Type of link in Roam (default: log)")
    parser.add_argument("-dt", required=True, help="The name of the record in the database")
    parser.add_argument("-dtl", required=True, help="The DT link to the record in the database")
    parser.add_argument("-db", help="The name of the database")
    parser.add_argument("-dbl", help="The link to the database")
    parser.add_argument("-c", help="A comment")
    parser.add_argument("-sc", help="A second comment to be nested under the block in Roam")

    args = parser.parse_args()

    result = link_roam(args.page_title, args.dt, args.dtl, args.db, args.dbl, args.t, args.c, args.sc)
    print(result)  # This will be captured by AppleScript

if __name__ == "__main__":
    main()