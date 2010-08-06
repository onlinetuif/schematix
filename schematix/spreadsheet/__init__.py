from schematix.core import SchemaExtractor, Table
from schematix.spreadsheet import parse, classify

class SpreadsheetExtractor(SchemaExtractor):
    def __init__(self, source, filename='', url=''):
        SchemaExtractor.__init__(self, source, filename, url)
        self.workbook = parse.load_spreadsheet(source)
        self.xls_tables = []
        self.labels = []
        self.scores = []

    def extract_schemas(self):
        self.xls_tables = parse.parse_workbook(self.workbook)
        (self.labels, self.scores) = classify.classify_tables(self.xls_tables)

    def get_tables(self):
        for i in range(len(self.xls_tables)):
            cells = self.xls_tables[i].cells
            #pprint([[c.value for c in row] for row in cells])
            #pprint([[c.data_type for c in row] for row in cells])
            #pprint([[c.style for c in row] for row in cells])
            #pprint([[c.fmt for c in row] for row in cells])
            #pprint(self.labels[i])
            #pprint(self.scores[i])
            new_table = Table.from_xls(cells, self.labels[i])
            new_table.clean()
            yield new_table

