
# Common library imports
import re
import os
import sys

# Command line parse imports
import argparse
import scrape_wiki_docs as docs

# XML and HTML parsing imports
import requests
from bs4 import BeautifulSoup

# Data manipulation import
import numpy as np
import pandas as pd

# Custom parsing import
from wikitable import WikiTable

def create_parser():
    '''
    '''
    parser = argparse.ArgumentParser(description = docs.help_text)
    parser.add_argument('-u', '--url', type = str, help = docs.help_url_text)
    parser.add_argument('-t', '--table', type = int, help = docs.help_tag_text)

    return parser


def main(argv):
    '''
    This function is automatically run if this script is called from the command line. It does the 
    following:

        1. Parses command line inputs for URLs and table tag
        2. Connects to the given URL and extracts the table
        3. Saves the table into csv format
    '''
    # Parse input arguments
    parser = create_parser()
    inputs = parser.parse_args(argv)

    sinclair_table = WikiTable(url = inputs.url, tab_num = inputs.table)
    table_df = sinclair_table.pandas_from_url(col_th = True)
    table_df.to_csv('sinclair_stations.csv', index = False)


if __name__ == '__main__':
    main(sys.argv[1:])
