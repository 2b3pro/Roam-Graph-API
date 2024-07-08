# -*- coding: utf-8 -*-
"""
Title:        link_dt-roam.py
Description:  Script to link DEVONthink items to Roam Research pages
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-07-06
Version:      4.4.0
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
from roam_utils import get_roam_date_format, process_block_text, find_nested_block, page_exists
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
def link_roam(page_title, dt, dtl, db=None, dbl=None, link_type="ref", c=None, sc=None):
    try:
        token = os.getenv('ROAM_API_TOKEN')
        graph = os.getenv('ROAM_GRAPH_NAME')

        if not token or not graph:
            raise ValueError("ROAM_API_TOKEN or ROAM_GRAPH_NAME not set in .env file")

        client = initialize_graph({'graph': graph, 'token': token})
        logger.debug("Roam client initialized")

        today = get_roam_date_format(datetime.now())

        # Check if the page exists
        page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]'))

        if not page_uid:
            # Create the page if it doesn't exist
            create_page(client, {'page': {'title': page_title}})
            time.sleep(3)  # Wait for page creation
            page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]'))
            if not page_uid:
                raise Exception(f"Failed to create page: {page_title}")

        # Check if the DEVONthink link already exists on the page
        existing_block = find_nested_block(client, f"({page_uid})", "References::", dtl)

        if existing_block and "error" not in existing_block:
            added_block_uid = existing_block["target_uid"]
            logger.debug(f"Preparing to add combined comments under {added_block_uid}")

            # Prepare the combined comment
            combined_comment = f"{c}\n{sc}".strip() if c and sc else (c or sc or "")

            if combined_comment:
                # Add the combined comment as a child of the existing block
                status_code, response_text = create_block(client, {
                    'location': {'parent-uid': added_block_uid, 'order': 0},
                    'block': {'string': process_block_text(combined_comment)}
                })
                logger.debug(f"Added combined comments under {added_block_uid}")
                if status_code != 200:
                    raise Exception(f"Failed to add comment to existing block. Status: {status_code}, Response: {response_text}")
        else:
            # If the block doesn't exist, create it
            references_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "References::"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]'))
            if not references_uid:
                status_code, response_text = create_block(client, {
                    'location': {'parent-uid': page_uid, 'order': 0},
                    'block': {'string': "References::"}
                })
                if status_code != 200:
                    raise Exception(f"Failed to create References:: block. Status: {status_code}, Response: {response_text}")
                references_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "References::"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]'))

            # Create the new block with DEVONthink link
            block_content = f"[{dt}]({dtl})"
            if db and dbl:
                block_content = f"[[{db}]({dbl})]—[{dt}]({dtl})"

            if c:
                block_content = f"{block_content} | {c}"

            status_code, response_text = create_block(client, {
                'location': {'parent-uid': references_uid, 'order': 0},
                'block': {'string': block_content}
            })
            if status_code != 200:
                raise Exception(f"Failed to create link block. Status: {status_code}, Response: {response_text}")

            # Get the UID of the newly created block
            added_block_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{block_content}"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]'))

            # Add comments if provided
            # combined_comment = f"{c}\n{sc}".strip() if c and sc else (c or sc or "")
            if sc:
                status_code, response_text = create_block(client, {
                    'location': {'parent-uid': added_block_uid, 'order': 0},
                    'block': {'string': process_block_text(sc)}
                })
                if status_code != 200:
                    raise Exception(f"Failed to create comment block. Status: {status_code}, Response: {response_text}")

        # Create/update the daily log entry
        today = get_roam_date_format(datetime.now())
        daily_page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :node/title "{today}"]]'))
        if not daily_page_uid:
            create_page(client, {'page': {'title': today}})
            time.sleep(3)
            daily_page_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :node/title "{today}"]]'))

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

        # Create the simplified daily log entry
        dailypagelog_pageref_block = f"[[{page_title}]] ⨠ (({added_block_uid}))"

        # Check to see if the entry already exists
        dailypagelog_block_uid = process_q_result(q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{dailypagelog_pageref_block}"] [?e :block/page ?p] [?p :block/uid "{daily_page_uid}"]]'))
        if not dailypagelog_block_uid:
            status_code, response_text = create_block(client, {
                'location': {'parent-uid': daily_log_block_uid, 'order': 0},
                'block': {'string': dailypagelog_pageref_block}
            })
            if status_code != 200:
                raise Exception(f"Failed to create daily log entry. Status: {status_code}, Response: {response_text}")

        roam_url = f"https://roamresearch.com/#/app/{graph}/page/{page_uid}"

        return json.dumps({
            "status": "success",
            "message": "Link created successfully",
            "dt_url": dtl,
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
    parser.add_argument("-t", choices=["log", "ref"], default="ref", help="Type of link in Roam (default: ref)")
    parser.add_argument("-dt", required=True, help="The name of the record in the database")
    parser.add_argument("-dtl", required=True, help="The DT link to the record in the database")
    parser.add_argument("-db", help="The name of the database")
    parser.add_argument("-dbl", help="The link to the database")
    parser.add_argument("-c", help="A citation or comment")
    parser.add_argument("-sc", help="A second comment (e.g. brief abstract) to be nested under the block in Roam")

    args = parser.parse_args()

    result = link_roam(args.page_title, args.dt, args.dtl, args.db, args.dbl, args.t, args.c, args.sc)
    print(result)  # This will be captured by AppleScript

if __name__ == "__main__":
    logger.debug("Starting the script")
    main()