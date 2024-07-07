import logging
from datetime import datetime
import time
import json
import os
import argparse
from dotenv import load_dotenv
from client import initialize_graph, q, create_page, create_block
from roam_utils import get_roam_date_format

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(message)s at Line %(lineno)d')
logger = logging.getLogger(__name__)

token = os.getenv('ROAM_API_TOKEN')
graph = os.getenv('ROAM_GRAPH_NAME')

client = initialize_graph({'graph': graph, 'token': token})


# Use the utilities
# create_page(client, {'page': {'title': get_roam_date_format(datetime.now()) }})
daily_page_uid = "07-07-2024"
today = get_roam_date_format(datetime.now())

log_block_uid = q(client, f'[:find ?uid . :where [?e :block/uid ?uid] [?e :block/string "[[Log/DEVONthink]]"] [?e :block/page ?p] [?p :block/uid "{daily_page_uid}"]]')
print(log_block_uid)

log_block_result = create_block(client, {
	'location': {'parent-uid': daily_page_uid, 'order': 0},
	'block': {'string': "[[Log/DEVONthink]]"}
})
print(f"Results from block creation: {log_block_result}")

