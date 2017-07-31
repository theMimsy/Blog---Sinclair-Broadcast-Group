
import json
import csv

import numpy as np
import pandas as pd

def generate_csv_from_json(json_path):
    '''
    '''
    # Open up the json file and load it as a dictionary
    with open(json_path, 'r') as json_in:
        json_in_data = json.load(json_in)

        # Make every row of the csv come from the values of the dictionary
        for key, val in json_in_data.items():
            yield val

def generate_json_from_csv(csv_data):
    '''
    '''
    sorted_data = csv_data.sort_index()
    for idx, row in sorted_data.iterrows():
        idx_str = str(idx)
        row_str = {str(key): str(val) for (key, val) in row.to_dict().items()}
        row_str['DMA Code'] = idx_str
        yield idx_str, row_str

def main():

    # We have old JSON but we don't have new JSON
    json_old_path = "tv.json"
    json_new_path = "tv_2017.json"

    # We have new CSV but we don't have old CSV
    csv_old_path = "tv.csv"
    csv_new_path = "tv_2017.csv"

    # Connection between old and new CSV
    merge_on = "Designated Market Area (DMA)"

    # Convert old JSON to old CSV
    csv_old_data = pd.DataFrame(generate_csv_from_json(json_old_path))
    csv_old_data = csv_old_data.set_index("DMA Code").sort_values(merge_on)
    csv_old_data.to_csv(csv_old_path, quoting = csv.QUOTE_ALL)

    # Use old CSV to patch missing data in new CSV
    csv_new_data = pd.read_csv(csv_new_path, dtype = object).sort_values(merge_on)
    csv_new_data.index = csv_old_data.index

    # Get new JSON from patched new CSV
    with open(json_new_path, 'w') as json_outfile:
        final_output = {k: v for (k, v) in generate_json_from_csv(csv_new_data)} 
        json.dump(final_output, json_outfile, 
                sort_keys = True, indent = 2, separators = (',', ': '))

if __name__ == "__main__":
    main()
