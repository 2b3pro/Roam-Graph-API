# -*- coding: utf-8 -*-
"""
Title:        link_dt-roam.py
Description:  Script to link DEVONthink items to Roam Research pages
Author:       Ian Shen
Email:        2b3pro@gmail.com
Date:         2024-10-31
Version:      4.4.6
License:      MIT

Usage:
    python link_dt-roam.py PAGE_TITLE -dt DT_NAME -dtl DT_LINK [-t {log,ref}] [-db DB_NAME] [-dbl DB_LINK] [-c COMMENT] [-sc SUBCOMMENT]

Required:
    PAGE_TITLE   Title of Roam Research page
    -dt          Name of DEVONthink record
    -dtl         Link to DEVONthink record

Optional:
    -t          Link type: 'ref' (default) or 'log'
    -db         DEVONthink database name
    -dbl        DEVONthink database link
    -c          Primary comment/citation
    -sc         Secondary comment (nested under main block)

Environment:
    Requires .env file with:
    - ROAM_API_TOKEN
    - ROAM_GRAPH_NAME
"""

import logging
import time
import json
import os
import sys
import argparse
import traceback
from datetime import datetime
from dotenv import load_dotenv
from roamClient import initialize_graph, q, create_page, create_block
from roam_utils import get_roam_date_format, process_block_text, find_nested_block, page_exists, process_q_result

logging.basicConfig(level=logging.ERROR, format='%(levelname)s - %(message)s')
logging.info("Starting script execution...")

load_dotenv()
logging.info("Loaded .env file")

def link_roam(page_title, dt, dtl, db=None, dbl=None, link_type="ref", c=None, sc=None):
    try:
        token = os.getenv('ROAM_API_TOKEN')
        graph = os.getenv('ROAM_GRAPH_NAME')
        logging.info(f"Got environment variables - Graph: {graph}")

        if not token or not graph:
            raise ValueError("ROAM_API_TOKEN or ROAM_GRAPH_NAME not set in .env file")

        logging.info("Initializing Roam client...")
        client = initialize_graph({'graph': graph, 'token': token})
        logging.info("Roam client initialized")

        today = get_roam_date_format(datetime.now())
        logging.info(f"Today's date in Roam format: {today}")

        # Check if the page exists
        logging.info(f"Checking if page exists: {page_title}")
        raw_page_query = q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
        logging.info(f"Raw page query result: {raw_page_query}")
        page_uid = process_q_result(raw_page_query)
        logging.info(f"Processed page_uid: {page_uid}")

        if not page_uid:
            logging.info(f"Page doesn't exist, creating: {page_title}")
            status_code = create_page(client, {'page': {'title': page_title}})
            if status_code != 200:
                raise Exception(f"Failed to create page. Status: {status_code}")
            time.sleep(3)  # Wait for page creation
            raw_page_query = q(client, f'[:find ?uid . :where [?e :node/title "{page_title}"] [?e :block/uid ?uid]]')
            logging.info(f"Raw page query result after creation: {raw_page_query}")
            page_uid = process_q_result(raw_page_query)
            logging.info(f"Processed page_uid after creation: {page_uid}")
            if not page_uid:
                raise Exception(f"Failed to create page: {page_title}")

        # Check if the DEVONthink link already exists on the page
        logging.info("Checking for existing DEVONthink link...")
        existing_block = find_nested_block(client, f"({page_uid})", "References::", dtl)
        logging.info(f"Existing block check result: {existing_block}")

        if existing_block and "error" not in existing_block:
            added_block_uid = existing_block["target_uid"]
            logging.info(f"Found existing block with UID: {added_block_uid}")

            combined_comment = f"{sc}".strip() if sc else ""

            if combined_comment:
                logging.info("Adding comment to existing block...")
                status_code = create_block(client, {
                    'location': {'parent-uid': added_block_uid, 'order': 0},
                    'block': {'string': process_block_text(combined_comment)}
                })
                logging.info(f"Add comment result - Status: {status_code}")
                if status_code != 200:
                    raise Exception(f"Failed to add comment to existing block. Status: {status_code}")
        else:
            logging.info("No existing block found, creating new one...")
            raw_refs_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "References::"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]')
            logging.info(f"Raw References:: query result: {raw_refs_query}")
            references_uid = process_q_result(raw_refs_query)
            logging.info(f"Processed references_uid: {references_uid}")

            if not references_uid:
                logging.info("Creating References:: block...")
                status_code = create_block(client, {
                    'location': {'parent-uid': page_uid, 'order': 0},
                    'block': {'string': "References::"}
                })
                logging.info(f"Create References:: block result - Status: {status_code}")
                if status_code != 200:
                    raise Exception(f"Failed to create References:: block. Status: {status_code}")
                raw_refs_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "References::"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]')
                logging.info(f"Raw References:: query result after creation: {raw_refs_query}")
                references_uid = process_q_result(raw_refs_query)
                logging.info(f"Processed references_uid after creation: {references_uid}")

            block_content = f"[{dt}]({dtl})"
            if db and dbl:
                block_content = f"[[{db}]({dbl})]—[{dt}]({dtl})"

            if c:
                block_content = f"{block_content} | {c}"

            logging.info(f"Creating block with content: {block_content}")
            status_code = create_block(client, {
                'location': {'parent-uid': references_uid, 'order': 0},
                'block': {'string': block_content}
            })
            logging.info(f"Create block result - Status: {status_code}")
            if status_code != 200:
                raise Exception(f"Failed to create link block. Status: {status_code}")

            # Get the UID of the newly created block
            raw_block_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{block_content}"] [?e :block/page ?p] [?p :block/uid "{page_uid}"]]')
            logging.info(f"Raw block query result: {raw_block_query}")
            added_block_uid = process_q_result(raw_block_query)
            logging.info(f"Processed added_block_uid: {added_block_uid}")

            # Add comments if provided
            if sc:
                logging.info(f"Adding comment: {sc}")
                status_code = create_block(client, {
                    'location': {'parent-uid': added_block_uid, 'order': 0},
                    'block': {'string': process_block_text(sc)}
                })
                logging.info(f"Add comment result - Status: {status_code}")
                if status_code != 200:
                    raise Exception(f"Failed to create comment block. Status: {status_code}")

        # Create/update the daily log entry
        logging.info("Creating daily log entry...")
        today = get_roam_date_format(datetime.now())
        raw_daily_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :node/title "{today}"]]')
        logging.info(f"Raw daily page query result: {raw_daily_query}")
        daily_page_uid = process_q_result(raw_daily_query)
        logging.info(f"Processed daily_page_uid: {daily_page_uid}")

        if not daily_page_uid:
            logging.info(f"Creating daily page: {today}")
            status_code = create_page(client, {'page': {'title': today}})
            if status_code != 200:
                raise Exception(f"Failed to create daily page. Status: {status_code}")
            time.sleep(3)
            raw_daily_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :node/title "{today}"]]')
            logging.info(f"Raw daily page query result after creation: {raw_daily_query}")
            daily_page_uid = process_q_result(raw_daily_query)
            logging.info(f"Processed daily_page_uid after creation: {daily_page_uid}")

        daily_parent_block_content = "[[Log/DEVONthink]]"
        raw_log_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{daily_parent_block_content}"] [?e :block/page ?p] [?p :block/uid "{daily_page_uid}"]]')
        logging.info(f"Raw log block query result: {raw_log_query}")
        daily_log_block_uid = process_q_result(raw_log_query)
        logging.info(f"Processed daily_log_block_uid: {daily_log_block_uid}")

        if not daily_log_block_uid:
            logging.info(f"Creating log block: {daily_parent_block_content}")
            status_code = create_block(client, {
                'location': {'parent-uid': daily_page_uid, 'order': 0},
                'block': {'string': daily_parent_block_content}
            })
            logging.info(f"Create log block result - Status: {status_code}")
            if status_code != 200:
                raise Exception(f"Failed to create {daily_parent_block_content} block. Status: {status_code}")
            raw_log_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{daily_parent_block_content}"] [?e :block/page ?p] [?p :block/uid "{daily_page_uid}"]]')
            logging.info(f"Raw log block query result after creation: {raw_log_query}")
            daily_log_block_uid = process_q_result(raw_log_query)
            logging.info(f"Processed daily_log_block_uid after creation: {daily_log_block_uid}")

        # Create the simplified daily log entry
        dailypagelog_pageref_block = f"[[{page_title}]] ⨠ (({added_block_uid}))"
        logging.info(f"Creating daily log entry: {dailypagelog_pageref_block}")

        # Check to see if the entry already exists
        raw_entry_query = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "{dailypagelog_pageref_block}"] [?e :block/page ?p] [?p :block/uid "{daily_log_block_uid}"]]')
        logging.info(f"Raw entry query result: {raw_entry_query}")
        dailypagelog_block_uid = process_q_result(raw_entry_query)
        logging.info(f"Processed dailypagelog_block_uid: {dailypagelog_block_uid}")

        if not dailypagelog_block_uid:
            status_code = create_block(client, {
                'location': {'parent-uid': daily_log_block_uid, 'order': 0},
                'block': {'string': dailypagelog_pageref_block}
            })
            logging.info(f"Create daily log entry result - Status: {status_code}")
            if status_code != 200:
                raise Exception(f"Failed to create daily log entry. Status: {status_code}")

        roam_url = f"https://roamresearch.com/#/app/{graph}/page/{page_uid}"
        logging.info(f"Operation completed. Roam URL: {roam_url}")

        return json.dumps({
            "status": "success",
            "message": "Link created successfully",
            "dt_url": dtl,
            "roam_url": roam_url
        })

    except Exception as e:
        logging.info(f"Error occurred: {str(e)}")
        logging.info(f"Traceback: {traceback.format_exc()}")
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

    logging.info("Starting main function...")
    logging.info(f"Arguments: {args}")
    result = link_roam(args.page_title, args.dt, args.dtl, args.db, args.dbl, args.t, args.c, args.sc)
    logging.info(f"Result: {result}")  # This will be captured by AppleScript

if __name__ == "__main__":
    logging.info("Script started")
    main()
