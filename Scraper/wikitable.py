# File:        wikitable.py
# Description: A parser specifically for extracting html tables from wikipedia.
# Author:      Dawid Minorczyk
# Date:        July 19 2017

# Libraries for parsing html and xml
import requests
from bs4 import BeautifulSoup

# Libraries for data management
import numpy as np
import pandas as pd

# Libraries for iteration and grouping
import itertools
import operator

# Want to use context management for optional values
from contextlib import contextmanager

class WikiTableOptions(dict):
    def __init__(self, kwargs):
        '''
        '''
        # Get defaults and override with user input
        options = self._default_options.copy()
        options.update(kwargs)

        # Apply overriden options to self
        dict.__init__(self, options)
        self.__dict__ = self

    # A class variable holding every option in WikiTable and their defaults
    _default_options = {
        'url'     : None,  'tab_num' : 0,
        'col_th'  : False, 'row_th'  : False,
        'col_ex'  : None,  'row_ex'  : None,  'log_ex'  : 'AND',
        'col_ref' : [],    'row_ref' : [],    'log_reg' : 'AND', 'on_link' : None
    }

    @property
    def default_options(self):
        '''
        The getter funtion for the `default_options` class variable. Always looks up the class
        variable as opposed to the instance variable.
        '''
        return type(self)._default_options

    @default_options.setter
    def default_options(self, value):
        '''
        The setter function for the `default_options` class variable. For the sake of expectant
        behavior, does not allow user to change default values.
        '''
        raise Exception('Default WikiTable options should not be modified')

    @contextmanager
    def updated(self, kwargs):
        '''
        '''
        # Save old options and override with new ones
        saved_options = self.copy()
        self.update(kwargs)

        # Return the new options as a context
        yield self

        # Revert new options to old options
        dict.__init__(self, saved_options)
        self.__dict__ = self
    
class WikiTable:
    '''
    An html parser based off of bs4.BeautifulSoup that extracts tables from a given url. The
    parser expects at least a url of the page containing the table. If there are more than one
    table on the page, the user can specify which one to extract, but only one is extracted per
    call to `WikiTable`. The output is a `pandas.DataFrame` object.

    Keyword arguments:
    url     -- A string containing the full path to the html page to parse. (default None)
    tab_num -- A zero indexed integer specifying which table to extract from the page. (default 0)
    col_th  -- A boolean specifying whether to treat <th></th> tags on the first row as columns of 
        the output `DataFrame`. If the first row contains <td></td> tags or a mix of <th></th> and
        <td></td> tags, then the <td></td> tags are ignored and not put in as column names.
        (default False)
    row_th  -- A boolean specifying whether to treat <th></th> tags on the first column as the
        index of the output `DataFrame`. If the first column contains <td></td> tags or a mix of 
        <th></th> tags and <td></td> tags, then the <td></td> tags are ignored and not integrated
        into the index. (default False)
    col_ex  -- A list of columns to extract from the table. If `None`, will extract all columns.
        (default None)
    row_ex  -- A list of rows to extract from the table. If `None`, will extract all rows.
        (default None)
    log_ex  -- A string that can take on values 'AND', 'OR', or 'XOR'. Specifies how the `col_ex`
        and `row_ex` arguments interact. 'AND' implies intesection of rows and columns, 'OR'
        implies the union of rows and columns, and 'XOR' implies the symmetric difference of rows
        and columns. (default 'AND')
    col_ref -- A list of columns from the table to check for hyperlinks. If a hyperlink is found, 
        the parser given by `on_link` will be used to extact more data. If `None`, will look at 
        all columns.  (default [])
    row_ref -- A list of rows from the table to check for hyperlinks. If a hyperlink is found, the
        parser given by `on_link` will be used to extract more data. If `None`, will look at all 
        rows. (default [])
    log_ref -- A string that can take on values 'AND', 'OR', or 'XOR'. Specifies how the `col_ref`
        and `row_ref` arguments interact. 'AND' implies intesection of rows and columns, 'OR'
        implies the union of rows and columns, and 'XOR' implies the symmetric difference of rows
        and columns. (default 'OR')
    '''
    def __init__(self, **kwargs):
        self._options = WikiTableOptions(kwargs)

    def pandas_from_url(self, **kwargs):
        '''
        '''
        # Temporarily update options for this operation
        with self._options.updated(kwargs) as options:
            # Get XML/HTML from source URL
            page = requests.get(options.url)

            # Extract
            soup = BeautifulSoup(page.content, 'lxml')
            table_soup = soup.find_all('table')[options.tab_num]

            # Turn over calculation to internal function
            return self._pandas_from_soup(table_soup, options)
    
    def pandas_from_soup(self, table_soup, **kwargs):
        '''
        '''
        # Temporarily update options for this operation
        with self._options.updated(kwargs) as options:

            # Turn over calculation to internal function
            return self._pandas_from_soup(table_soup, options)

    def _pandas_from_soup(self, table_soup, options):
        '''
        '''
        # Make a list of rows in the table
        tr_soup_list = table_soup.find_all('tr')

        # Parse through the first row for header information
        col_idx = self._handle_col_th(tr_soup_list, options)
        row_idx = self._handle_row_th(tr_soup_list, options)
        table_generator = self._generate_body(tr_soup_list, options)

        return pd.DataFrame(data = table_generator, index = row_idx, columns = col_idx)

    def _th_check(self, elem_default, elem_soup):
        '''
        '''
        if elem_soup.name == 'th':
            return self.get_clean_text_from_soup(elem_soup)
        else:
            return elem_default 

    def _handle_col_th(self, tr_soup_list, options):
        '''
        '''
        # First row of the given table
        th_td_soup_list = tr_soup_list[0].find_all(['th', 'td'])

        # Default column names
        col_idx = list( range(len(th_td_soup_list)) )

        # Parse in column names depending on options
        if options.col_th:
            for idx, th_td_soup in enumerate(th_td_soup_list):
                col_idx[idx] = self._th_check(idx,  th_td_soup)
            return col_idx
        else:
            return col_idx
    
    def _handle_row_th(self, tr_soup_list, options):
        '''
        '''
        # Default row names
        start_row = 1 if options.col_th else 0
        row_idx = list( range(len(tr_soup_list) - start_row) )

        # Parse in row names depending on options
        if options.row_th:
            #First column of the given table
            th_td_soup_list = [x.find(['th', 'td']) for x in tr_soup_list[start_row:]]

            for idx, th_td_soup in enumerate(th_td_soup_list):
                row_idx[idx] = self._th_check(idx,  th_td_soup)
            return row_idx
        else:
            return row_idx

    def _save_row_col_span(self, row, col, cell_soup, row_col_spans):
        '''
        '''
        has_rowspan = cell_soup.has_attr('rowspan')
        has_colspan = cell_soup.has_attr('colspan')
        has_both = has_rowspan & has_colspan

        if has_both:
            colspan = int(cell_soup.get('colspan'))
            colspan_list = list(range(colspan))
            rowspan = int(cell_soup.get('rowspan'))
            rowspan_list = list(range(rowspan))

            for r_off, c_off in itertools.product(colspan_list, rowspan_list):
                row_col_spans[(row + r_off, col + c_off)] = \
                        self.get_clean_text_from_soup(cell_soup)
            return

        if has_rowspan:
            rowspan = int(cell_soup.get('rowspan'))

            for r_off in range(rowspan):
                row_col_spans[(row + r_off, col)] = \
                        self.get_clean_text_from_soup(cell_soup)
            return

        if has_colspan:
            colspan = int(cell_soup.get('colspan'))

            for c_off in range(colspan):
                row_col_spans[(row, col + c_off)] = \
                        self.get_clean_text_from_soup(cell_soup)
            return

    def _load_row_col_span(self, row, col, row_col_spans):
        '''
        '''
        # Get all of the spanned cells in this row following this columns
        repeat_cells = [(r, c) for (r, c) in row_col_spans.keys() if r == row and c >= col]
        repeat_cells = sorted(repeat_cells, key = operator.itemgetter(1)) # Sort by column

        # No more spanned cells in this row
        if not repeat_cells:
            # print('Location:', row, col)
            # print('Cells:   ', repeat_cells)
            return []

        # We will work with just to columns
        repeat_cols = [c for (r, c) in repeat_cells]

        if repeat_cols[0] != col and repeat_cols[0] != col + 1:
            return []

        # Magic groupby and tuple indexing
        continuous_groups = itertools.groupby(enumerate(repeat_cols), key = lambda i: i[1] - i[0])
        next_repeat_cells = list( next( continuous_groups )[1] )
        next_repeat_cells = [(row, c) for (i, c) in next_repeat_cells]
        next_repeat_phrases = [row_col_spans[key] for key in next_repeat_cells]
        # print('Location:', row, col)
        # print('Cells:   ', repeat_cells)
        # print('Grouped: ', next_repeat_cells)
        # print(next_repeat_phrases)
        return next_repeat_phrases

    def _generate_body(self, tr_soup_list, options):
        '''
        '''
        # Take care of header options 
        start_row = 1 if options.col_th else 0 # Start at later row if we have col index
        start_col = 1 if options.row_th else 0 # Start at later col if we have row index

        # Dictionary to keep track of colspan and rowspan information
        row_col_spans = {}

        # Iterate over all rows and columns to generate data
        for row_idx, tr_soup in enumerate(tr_soup_list[start_row:]):

            # Check for previous colspans and rowspans
            to_yield = self._load_row_col_span(row_idx, 0, row_col_spans)
            col_off = len(to_yield)

            td_soup_list = tr_soup.find_all(['th', 'td'])
            for col_raw, td_soup in enumerate(td_soup_list[start_col:]):

                # Calculate col offset due to spans
                col_idx = col_raw + col_off

                # Check for previous colspans and rowspans
                if col_raw:
                    repeat_cells = self._load_row_col_span(row_idx, col_idx, row_col_spans)
                    to_yield += repeat_cells
                    col_off += len(repeat_cells)

                # Recalculate col offset
                col_idx = col_raw + col_off

                # Save off any colspans and rowspans for future cells
                self._save_row_col_span(row_idx, col_idx, td_soup, row_col_spans)

                # Add cell to yielding array
                cell_str = self.get_clean_text_from_soup(td_soup)
                to_yield.append(cell_str)

            yield to_yield

    def _generate_filtered_body(self, body_generator, options):
        '''
        '''
        pass

    def get_clean_text_from_soup(self, td_soup):
        '''
        '''
        # Tags that we want to remove from td
        tag_list = ['sup', 'small', 'br']

        # Remove child tags
        for tag in tag_list:
            if td_soup.find_all(tag):
                exec('td_soup.' + tag + '.extract()')

        # Extract the text
        to_return = td_soup.get_text()

        # Clean it up
        to_return = to_return.strip()
        to_return = to_return.replace('\n', '')
        to_return = to_return.replace('\u2013', '-')

        return to_return

    def follow_links(self, parser, **kwargs):
        with self._options.updated(kwargs) as options:
            pass
