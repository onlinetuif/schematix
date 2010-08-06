from schematix.classify_util import BaseClassifier, RowScore, HEADER_DICT
from schematix.html_table.parse import HTMLCell

def classify_tables(tables):
    classifier = HTMLClassifier()
    result = [classifier.classify(t) for t in tables]
    return zip(*result)

class HTMLClassifier(BaseClassifier):
    def compute_metadata_score(self, row):
        score = 0.0
        for i, cell in enumerate(row):
            if cell.is_empty():
                score += .8
            elif cell.is_merged():
                score += .7
            elif i > 1:
                if (cell.data_type == 'TEXT' and len(cell.value) > 20):
                    score += .5 
                elif (cell.style.get('font-weight','normal') != 'normal' or
                      cell.style.get('font-style','normal') != 'normal'):
                    score += .25
        cell_count = len(row)
        if cell_count == 0:
            return 0.0
        return score / cell_count

    def compute_sim_score(self, row, next_row):
        attrs_match = self.attrs_match
        if next_row is None:
            return 0.0
        score = 0.0
        for cell, next_cell in zip(row, next_row):
            if cell.is_empty() or next_cell.is_empty():
                score += .2
                continue
            cell_score = 0.0
            # TODO: add 4 if numeric formatting is the same
            if cell.fmt and cell.fmt == next_cell.fmt:
                cell_score += 2
                if cell.fmt in ('$','%'):
                    cell_score += 2
            # add 2 if cells have same type, otherwise subtract 4
            if cell.data_type == next_cell.data_type:
                cell_score += 3
            if cell.is_merged() != next_cell.is_merged():
                cell_score -= 3
            if cell.is_merged():
                cell_score -= 7
            if cell.style.get('row_group') in ('thead','tfoot'):
                cell_score -= 5
            # TODO: rewrite tests by iterating through (attr, weight) tuples
            if attrs_match(cell, next_cell, 'font-weight'):
                cell_score += 1
            if attrs_match(cell, next_cell, 'font-style'):
                cell_score += 1
            if attrs_match(cell, next_cell, 'text-align'):
                cell_score += 1
            if attrs_match(cell, next_cell, 'color'):
                cell_score += 1
            if attrs_match(cell, next_cell, 'background-color'):
                cell_score += 1
            score += cell_score / 8.0
        # return average score
        col_count = max(len(row), len(next_row), 3)
        return score / col_count

    def compute_header_score(self, row, next_row, row_num):
        attrs_match = self.attrs_match
        BLANK_CELL = HTMLCell('', None, '', None, {})
        if next_row is None:
            return 0.0
        
        row_score = 0.0
        #row_weight = 0.0

        next_row_padded = next_row + [BLANK_CELL for _ in
                                      range(len(row)-len(next_row))]

        for cell, next_cell in zip(row, next_row_padded): 
            if cell.is_empty() and next_cell.is_empty():
                row_score += .3
                continue
            if cell.is_empty() and not next_cell.is_empty():
                continue

            # TODO: add 3 if next_cell is DATE, and cell is not DATE
            features = [
                (cell.text in HEADER_DICT, 10, 0),
                (row_num == 0, 5, 0),
                (row_num == 1, 3, 0),
                (row_num == 2, 1, 0),
                (cell.style.get('row_group') == 'thead', 10, 0),
                (cell.tag == 'th', 10, 1),
                (cell.is_merged() and not next_cell.is_merged(), 8, 1),
                (cell.data_type != next_cell.data_type, 8, 1),
                (cell.data_type == 'TEXT' and 
                 next_cell.data_type == 'NUMBER', 12, 1),
                (cell.style.get('font-weight') == 'bold' or
                 cell.style.get('font-style') == 'italic', 3, 1),
                (not attrs_match(cell, next_cell, 
                                 ['font-weight','font-style']), 5, 1),
                (not attrs_match(cell, next_cell, 'text-align'), 5, 1),
                (not attrs_match(cell, next_cell, 
                                 ['color','background-color']), 5, 1)]

            pos_score = neg_score = 0.0
            for test, pos, neg in features:
                if test:
                    pos_score += pos
                else:
                    neg_score += neg
            cell_score = pos_score / (pos_score + neg_score)
            row_score += cell_score
            #row_score += cell_score * (1 + pos_score + neg_score)
            #row_weight += (1 + pos_score + neg_score)

        adjustment = 0.0
        if len(row) > 0:
            pct_merged = (1.0 * sum([1 for cell in row 
                                     if cell.merged != 'SINGLE']) 
                          / len(row))
            if pct_merged > .9:
                adjustment -= 0.15

        #if row_weight == 0:
        #    return 0.0
        #return row_score / row_weight + adjustment
        col_count = max(len(row), len(next_row))
        if col_count == 0:
            return 0.0
        return row_score / col_count + adjustment

    def get_out_of_block_label(self, row_num, row, next_row):
        if (row.header < 0.3 and
            row.sim_below > 0.9):
            return 'DATA'
        elif (row.header < 0.7 and
              row.sim_below < .1):
            return 'METADATA'
        elif (row.header > 0.5 and
              row.header > next_row.header and
              row.metadata < 0.45):
            return 'HEADER'
        elif (row_num == 0 and 
              row.metadata < 0.5 and
              row.header > 0.4 and
              row.header > next_row.header):
            return 'HEADER'
        else:
            return 'METADATA'

    def get_in_block_label(self, row_num, row, next_row):
        if (row.sim_above > 0.7):
            return 'DATA'
        elif row.header > 0.5:
            return 'SUBHEADER'
        elif row.sim_above > 0.3:
            return 'DATA'
        else:
            return 'UNKNOWN'
