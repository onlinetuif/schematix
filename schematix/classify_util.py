"""Base utilities for schematix extractors"""

HEADER_DICT = [
        'definition',
        'description',
        'notes',
        'name',
        'title',
        'type',
        'url',
        # Numeric
        'id',
        'amount',
        'total',
        'number',
        'value',
        'percent',
        'age',
        # Time
        'date',
        'month',
        'year',
        # Geog
        'address',
        'city',
        'state',
        'zipcode',
        ]

class RowScore(object):
    def __init__(self, empty, metadata, sim_above, sim_below, header):
        self.empty = empty
        self.metadata = metadata
        self.sim_above = sim_above
        self.sim_below = sim_below
        self.header = header

class BaseClassifier(object):
    def __init__(self):
        self.labels = []
        self.scores = []

    def classify(self, table):
        self.compute_row_scores(table.cells)
        self.assign_labels()
        self.assign_subheader_labels()
        return (self.labels, self.scores)

    def compute_row_scores(self, cells):
        scores = []
        row_iter = zip(cells,
                       cells[1:] + [None],
                       [None] + cells[:-1],
                       range(len(cells)))
        for row, next_row, prev_row, row_num in row_iter:
            empty = self.check_for_empty_row(row)
            metadata = self.compute_metadata_score(row)
            sim_above = self.compute_sim_score(row, prev_row)
            sim_below = self.compute_sim_score(row, next_row)
            header = self.compute_header_score(row, next_row, row_num)
            scores.append((empty, metadata, sim_above, sim_below, header))
        self.scores = scores

    def compute_metadata_score(self, row):
        pass

    def compute_sim_score(self, row, next_row):
        pass

    def compute_header_score(self, row, next_row, row_num):
        pass

    def check_for_empty_row(self, row):
        for cell in row:
            if not cell.is_empty():
                return False
        return True

    def attrs_match(self, cell1, cell2, style_attr):
        if not hasattr(style_attr,'__iter__'):
            style_attr = [style_attr]
        return all([cell1.style.get(s) == cell2.style.get(s) 
                    for s in style_attr])

    def assign_labels(self):
        scores = self.scores
        labels = ['UNKNOWN' for row in scores]

        in_block = False
        
        for i in range(len(scores)):
            row = RowScore(*scores[i])
            if i < len(scores) - 1:
                next_row = RowScore(*scores[i+1])
            else:
                next_row = RowScore(0, 0, 0, 0, 0)

            if row.empty:
                labels[i] = 'EMPTY'
                if labels[i-1] == 'EMPTY':
                    in_block = False
            elif not in_block:
                labels[i] = self.get_out_of_block_label(i, row, next_row)
                if labels[i] in ['HEADER','DATA']:
                    in_block = True
            else:
                labels[i] = self.get_in_block_label(i, row, next_row)
        self.labels = labels

    def get_out_of_block_label(self, row_num, row, next_row):
        pass

    def get_in_block_label(self, row_num, row, next_row):
        pass

    def assign_subheader_labels(self):
        # loop through rows, when you find a header, go up from it and 
        # down from it, changing METADATA to SUBHEADER
        scores, labels = self.scores, self.labels
        for i, label in enumerate(labels):
            if label in ['HEADER']:
                r = i - 1
                while (r > 0 and 
                       labels[r] in ['METADATA','SUBHEADER'] and 
                       scores[r][3] > 0.5):
                    labels[r] = 'SUBHEADER'
                    r -= 1
                r = i + 1
                while (r < len(labels) and 
                       labels[r] in ['METADATA','SUBHEADER'] and 
                       scores[r][3] > 0.5):
                    labels[r] = 'SUBHEADER'
                    r += 1

