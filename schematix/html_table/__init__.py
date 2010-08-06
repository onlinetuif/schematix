from schematix.core import SchemaExtractor, Table

from schematix.html_table import parse, classify

class HtmlTableExtractor(SchemaExtractor):
    """Schema Extractor for HTML table data"""
    def __init__(self, source, filename='', url=''):
        SchemaExtractor.__init__(self, source, filename, url)
        self.html = parse.load_html(source)
        self.html_tables = []
        self.labels = []
        self.scores = []

    def extract_schemas(self):
        self.html = parse.put_css_inline(self.html, self.url)
        self.html_tables = parse.parse_page(self.html)
        (self.labels, self.scores) = classify.classify_tables(self.html_tables)

    def get_tables(self):
        num_tables = len(self.html_tables)
        for i in range(num_tables):
            new_table = Table.from_html(self.html_tables[i].cells, 
                                        self.labels[i])
            new_table.clean()
            yield new_table

