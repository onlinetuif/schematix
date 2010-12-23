"""Base utilities for schematix extractors"""

import re

RE_FMT = re.compile('[\$0-9#\.\,]')
RE_NUM = re.compile('[\%#0-9\.\,]')
RE_ALPHA = re.compile('[A-z]')
RE_YEAR = re.compile('[1-2][0-9][0-9][0-9]')

def check_for_empty_row(row):
    for cell in row:
        if not cell.is_empty():
            return False
    return True

class BaseTable(object):
    def clean(self):
        """Remove empty columns and rows"""
        self.remove_empty_cols()
        self.remove_empty_rows()

    def remove_empty_cols(self):
        """Locate empty columns (where all cells are blank or empty), and 
        remove them"""
        cols_to_remove = []
        if len(self.cells) == 0:
            return
        for col_num in range(len(self.cells[0])):
            if all([row[col_num].is_empty() for row in self.cells]):
                cols_to_remove.append(col_num)
        for col_num in cols_to_remove[::-1]:
            self.remove_column(col_num)

    def remove_column(self, col_num):
        """Remove all cells in specified column from self.cells"""
        new_cells = []
        for row in self.cells:
            new_row = row[:col_num] + row[col_num+1:]
            new_cells.append(new_row)
        self.cells = new_cells

    def remove_empty_rows(self):
        """Locate empty rows and remove them"""
        new_cells = []
        for row in self.cells:
            if not all([cell.is_empty() for cell in row]):
                new_cells.append(row)

        self.cells = new_cells

class BaseCell(object):
    def __init__(self, text, value, data_type, fmt, style):
        """Initialize Cell object"""
        self.text = text # string representation of cell contents
        self.value = value # actual value of cell in native data type
        self.data_type = data_type # ['BLANK','EMPTY','DATE','TEXT','NUMBER']
        self.fmt = fmt # encoding for the translation between text and value
        self.style = style # dictionary of style attributes
        self.merged = 'SINGLE'

    def is_empty(self):
        """Test whether the cell is empty"""
        return (self.text == '' or
                self.data_type in ['BLANK','EMPTY'])

    def is_merged(self):
        """Test whether the cell is part of a merged cell block"""
        return (self.merged in ['PARENT','CHILD'])

    def numeric_score(self):
        """ Return a score that represents the numeric "strength" of a cell.
        
        0.0 = Definitely not a number (text, etc)
        0.5 = Blank cell or a number that looks like a year, etc
        0.9 = Non-year value, but no numeric formatting
        1.0 = Definitely a numeric quantity
        """
        if self.is_empty():
            return 0.5
        looks_like_year = RE_YEAR.search(self.text)
        looks_numeric = (RE_NUM.search(self.text) and
                         not RE_ALPHA.search(self.text))
        if self.fmt:
            numeric_format = RE_FMT.search(self.fmt)
        else:
            numeric_format = False

        #print 'self.txt: %s, self.fmt: %s' % (self.text, self.fmt)
        #print 'looks_like_year: %r, looks_numeric: %r, numeric_format: %r' % (
        #    looks_like_year, looks_numeric, numeric_format)

        if looks_like_year:
            return 0.5
        elif looks_numeric and numeric_format:
            return 1.0
        elif looks_numeric:
            return 0.9
        else:
            return 0.0

