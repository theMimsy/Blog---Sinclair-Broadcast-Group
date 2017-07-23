# Data manipulation import
import numpy as np
import pandas as pd

# Custom parsing import
from wikitable import WikiTable

def main():

    URL = 'https://en.wikipedia.org/wiki/List_of_stations_owned_or_operated_by_Sinclair_Broadcast_Group'

    stations_table = WikiTable(
        tab_num = 0, 
        regex_ex = ['Transmitter.*'], 
        regex_pos = [(0, 1)]
    )
    sinclair_table = WikiTable(
        url = URL, 
        tab_num = 1,
        col_ref = [1],
        col_th = True,
        on_link = stations_table
    )
    table_df = sinclair_table.pandas_from_url()
    table_df.to_csv('sinclair_stations.csv', index = False)

if __name__ == '__main__':
    main()
