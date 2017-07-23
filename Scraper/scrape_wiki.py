# General parsing support
import re

# Data manipulation import
import numpy as np
import pandas as pd
import csv

# Custom parsing import
from wikitable import WikiTable

def main():

    URL = 'https://en.wikipedia.org/wiki/List_of_stations_owned_or_operated_by_Sinclair_Broadcast_Group'

    # Recursive lookup
    stations_table = WikiTable(
        tab_num = 0, 
        regex_ex = ['Transmitter.*'], 
        regex_pos = [(0, 1)]
    )

    # Root lookup
    sinclair_table = WikiTable(
        url = URL, 
        tab_num = 1,
        col_ref = [1],
        col_th = True,
        on_link = stations_table
    )

    # Gather the data
    table_df = sinclair_table.pandas_from_url()

    # Fix the data up
    table_df.columns = ['Market', 'Station', 'Channel(RF)', 'Year', 
            'DF1', 'DF2', 'DF3', 'DF4', 'Power', 'Location']

    # Extract latitute and longitude information
    lat_lon_re_str = '(?P<Latitute>\d+\.\d+);\s+(?P<Longitude>-\d+.\d+)'
    lat_lon_df = table_df.Location.str.extract(lat_lon_re_str, expand = True)
    table_df = pd.concat([table_df, lat_lon_df], axis = 1)

    # Extract power information
    power_re_str = '(?P<Power>\d[,.\d]+\s+kW)'
    table_df.Power = table_df.Power.str.extract(power_re_str, expand = True)

    # Extract station information
    station_re_str = '\s*(?P<Station>[\w-]+)'
    table_df.Station = table_df.Station.str.extract(station_re_str, expand = True)

    # Clean up text
    for col_name in table_df:
        table_df[col_name] = table_df[col_name].str.strip()

    table_df.to_csv('sinclair_stations.csv', index = False, quoting = csv.QUOTE_ALL)

if __name__ == '__main__':
    main()
