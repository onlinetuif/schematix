from schematix import import_spreadsheet, SpreadsheetExtractor

TEST_DIR = "/".join(__file__.split("/")[:-1]) + "/"
FILENAME = 'test1.xls'

FILENAME = TEST_DIR + FILENAME

f = open(FILENAME)
s = SpreadsheetExtractor(f)
s.extract_schemas()
tables = list(s.get_tables())

from pprint import pprint

def test_filename_import():
    tables_from_filename = import_spreadsheet(FILENAME)

def test_metadata():
    assert len(tables) == 4
    print tables[0].dim

def test_sheet1_parsing():
    #print tables[0].get_header(0)
    #print tables[0].get_header(1)
    #print tables[0].get_header(2)
    #print tables[0].get_cell_val(0,0)
    #print tables[0].get_cell_val(0,1)
    assert tables
    t = tables[0]
    # Sheet 1
    assert t.dim == (7,8)
    assert t.get_header(0) == 'ID Value'
    assert t.get_header(6) == 'Age'

def test_sheet2_parsing():
    assert tables
    t = tables[1]
    # Sheet 2
    t.show_text()
    assert t.get_header(2) == 'National Rank'

def test_sheet3_parsing():
    assert tables
    t = tables[2]
    scores = s.scores[2]
    labels = s.labels[2]
    # Sheet 3
    t.show_text()
    pprint(zip(scores,labels))
    assert t.dim == (5,25)
    #assert 'Mail Participation Rates' in t.get_header(3)
    assert '2010' in t.get_header(3)

def test_data_parsing():
    print '%r, %r' % (tables[0].get_cell_val(0,0),
                      tables[0].get_cell_display_val(0,0))
    assert tables[0].get_cell_val(0,0) == 1.0
    assert tables[0].get_cell_display_val(0,0) == '1'
#    assert row_info_values == [1.0,'John','Smith','Boston','MA',
#                               'United States',24.0]
#    assert row_info_disp_vals == ['1','John','Smith','Boston','MA',
#                                  'United States','24']

def test_bad_file():
    bad_file = TEST_DIR + 'test1.html'
    g = open(bad_file)
    bad_tables = import_spreadsheet(g)
    assert len(list(bad_tables)) == 0

if __name__ == '__main__':
    test_filename_import()
    test_metadata()
    test_sheet1_parsing()
    test_sheet2_parsing()
    test_sheet3_parsing()
    test_data_parsing()
