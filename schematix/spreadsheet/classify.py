"""Module for scoring and classifying rows of spreadsheet (XLS) files"""

#from schematix import xlrd_util
from schematix.classify_util import BaseClassifier, HEADER_DICT
#from schematix.base_util import RowScore, HEADER_DICT
#from schematix.base_util import check_for_empty_row

def classify_tables(tables):
    classifier = XLSClassifier()
    result = [classifier.classify(t) for t in tables]
    print result
    if result:
        return zip(*result)
    else:
        return ([], [])

class XLSClassifier(BaseClassifier):
    def compute_metadata_score(self, row):
        """Returns "probability" that specified row is metadata""" 
        score = 0.0
        for i, cell in enumerate(row):
            if cell.is_empty():
                score += 1
            elif cell.is_merged():
                score += 1
            elif i > 1:
                score -= .75
                if (cell.data_type == 'TEXT' and len(cell.value) > 20):
                    score += 1
                elif (cell.style.get('bold') == 1 or
                      cell.style.get('italic') == 1):
                    score += 1
        cell_count = len(row)
        if cell_count == 0:
            return 0.0
        return score / cell_count

    def compute_sim_score(self, row, next_row):
        """Computes row similarity score; a weighted measure of how many
        attributes the cells of row share with the cells of next_row"""
        if next_row is None:
            return 0.0

        score = 0.0

        for cell, next_cell in zip(row, next_row):
            if cell.is_empty() or next_cell.is_empty():
                score += 2
                continue
            else:
                score -= .25

            if cell.fmt == next_cell.fmt:
                score += 4

            if cell.data_type == next_cell.data_type:
                score += 2
            else:
                score -= 4

            # TODO: implement is_numeric
            if cell.numeric_score() != next_cell.numeric_score():
                score -= 4

            # add 2 if same font, italics, color, or alignment
            if cell.style.get('font') == next_cell.style.get('font'):
                score += 2
            if cell.style.get('italic') == next_cell.style.get('italic'):
                score += 2
            if cell.style.get('color_idx') == next_cell.style.get('color_idx'):
                score += 2
            if cell.style.get('alignment') == next_cell.style.get('alignment'):
                score += 2

            # check merge similarity
            if cell.is_merged() and next_cell.is_merged():
                score += 2
            elif cell.is_merged() or next_cell.is_merged():
                score -= 8
            
        col_count = len(row)
        return score / col_count / 14

    def compute_header_score(self, row, next_row, row_num):
        """Computes header score; a measure of how similar the row is
        to an "ideal" header row"""
        score = 0.0

        if next_row is None:
            return score

        for cell, next_cell in zip(row, next_row):
            if cell.is_empty():
                score -= 1
                if next_cell.is_empty():
                    continue
                # TODO: if cell is empty, hope that there is a non-empty
                # cell above
                else:
                    score -= 4
            # TODO: if cell is identical to neighbor, hope that there is a
            # row above with non-identical values
            #elif False:
            #    pass

            else:
                score += 1

            if (cell.fmt != next_cell.fmt or
                cell.data_type != next_cell.data_type):
                score += 1

            if cell.data_type != 'DATE' and next_cell.data_type == 'DATE':
                score += 3

            if (cell.numeric_score() <= 0.5 and
                next_cell.numeric_score() > 0.5):
                score += 3

            if cell.text.lower() in HEADER_DICT:
                score += 3

            #TODO: implement calculate_sequence_score on new cells
            #score -= 10 * calculate_sequence_score(cell, next_cell)
            score -= cell.numeric_score()

            score += cell.style.get('bold') == 1
            score += cell.style.get('italic') == 1
            score += cell.style.get('bold') != next_cell.style.get('bold')
            score += cell.style.get('font') != next_cell.style.get('font')
            score += (cell.style.get('color_idx') != 
                      next_cell.style.get('color_idx'))
            score += (cell.style.get('alignment') != 
                      next_cell.style.get('alignment'))

        col_count = len(row)
        score = score / col_count / 4.0

        if row_num == 0:
            score += 0.3
        elif row_num == 1:
            score += 0.2
        elif row_num == 2:
            score += 0.1

        return score

    def get_out_of_block_label(self, row_num, row, next_row):
        if row.metadata < 0.2 and row.header < 0.2:
            return 'METADATA'
        elif (row.header > 0.5 and next_row.header < row.header):
            return 'HEADER'
        elif (row.header < 0.3 and row.sim_below > 0.9):
            return 'DATA'
        else:
            return 'METADATA'

    def get_in_block_label(self, row_num, row, next_row):
        if row.header > 1.0 and row.sim_above < 0.8:
            return 'HEADER'
        elif row.sim_above > 0.4:
            return 'DATA'
        else:
            return 'UNKNOWN'

def calculate_sequence_score(cells, row, col):
    """Determines whether the specified cell is part of an increasing
    sequence of numbers.
    """
    cell = cells[row][col]

    if cell['type'] != 'NUMBER':
        return 0.0

    try:
        cell_above = cells[row-1][col]
    except KeyError:
        cell_above = None
    try:
        cell_below = cells[row+1][col]
    except KeyError:
        cell_below = None
    
    if cell['value'] == 1:
        if cell_below['value'] == 2:
            return 1.0
    elif (cell_above['type'] == 'NUMBER' and
          cell_below['type'] == 'NUMBER' and
          cell_above['value']+1 == cell['value'] == cell_below['value']-1):
        return 1.0
    return 0.0

