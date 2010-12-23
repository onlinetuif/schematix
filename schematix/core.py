# for debugging
import pprint as _pprint
def pprint(text):
    _pprint.pprint(text, width=130)

class SchemaExtractor(object):
    """Base class for different parser types"""
    def __init__(self, source, filename='', url=''):
        if isinstance(source, basestring):
            if source.startswith('http://'):
                self.url = source
                self.filename = filename
            else:
                self.filename = source
                self.url = url
        else:
            self.filename = filename
            self.url = url
    
    def extract_schemas(self):
        pass

    def get_tables(self):
        pass

class Table(object):
    # headers = ('ID','Name','Value','Date','Cost')
    # values = [(1,'Tom',8,...),(...),(...)]
    # display_values = [('1','Tom','8.0',...),(...),(...)]
    def __init__(self, cells, labels):
        self.headers = []
        self.values = []
        self.display_values = []
        for i, row in enumerate(cells):
            if labels[i] == 'HEADER':
                for c in row:
                    self.headers.append(c.text)
            elif labels[i] == 'DATA':
                new_values = []
                new_display_values = []
                for c in row:
                    new_values.append(c.value)
                    new_display_values.append(c.text)
                self.values.append(tuple(new_values))
                self.display_values.append(tuple(new_display_values))

    @classmethod
    def from_xls(cls, cells, labels):
        return Table(cells, labels)

    @classmethod
    def from_html(cls, cells, labels):
        return Table(cells, labels)

    @property
    def dim(self):
        return (len(self.headers), len(self.values))

    def get_header(self, col):
        return self.headers[col]

    def get_cell_val(self, row, col):
        return self.values[row][col]

    def get_cell_display_val(self, row, col):
        return self.display_values[row][col]

    def show_text(self):
        print ','.join(self.headers).encode('ascii', 'ignore')
        for row in self.display_values:
            print ','.join(('"%s"' % cell_val for cell_val in
                            row)).encode('ascii','ignore')

    def show_values(self):
        print ','.join(self.headers)
        for row in self.values:
            print ','.join((unicode[v] for v in row))

    def get_html(self):
        from cgi import escape
        html = []
        html.append('<table>')
        html.append('<thead><tr><th>')
        h_list = '</th><th>'.join((escape(v)
                                   for v in self.headers))
        html.append(h_list.encode("ascii", "xmlcharrefreplace"))
        html.append('</th></tr></thead><tbody>')
        for row, row_vals in zip(self.display_values, self.values):
            html.append('<tr>')
            for cell, val in zip(row, row_vals):
                if (isinstance(val, int) or
                    isinstance(val, float)):
                    html.append('<td align="right">')
                else:
                    html.append('<td>')
                html.append(escape(cell).encode("ascii",
                                                "xmlcharrefreplace")) 
                html.append('</td>')
            html.append('</tr>')
        html.append('</tbody></table>')
        return ''.join(html)

    def show_html(self):
        print self.get_html()

    def __html__(self):
        return self.get_html()

    def clean(self):
        self.remove_empty_columns()

    def remove_empty_columns(self):
        remove_cols = []
        for i, col in enumerate(zip(*self.display_values)):
            #pprint(col)
            max_length = max((len(cell) for cell in col))
            if max_length == 0:
                remove_cols.append(i)
        
        new_headers = [h for i, h in enumerate(self.headers) if i not in
                       remove_cols]
        new_display_values = []
        new_values = []
        for i, (d, v) in enumerate(zip(self.display_values, self.values)):
            new_d = [k for j, k in enumerate(d) if j not in remove_cols]
            new_v = [k for j, k in enumerate(v) if j not in remove_cols]
            new_display_values.append(new_d)
            new_values.append(new_v)

        self.headers = new_headers
        self.display_values = new_display_values
        self.values = new_values


    @property
    def is_relational(self):
        return (len(self.headers) > 2 and
                len(self.values) > 2)
