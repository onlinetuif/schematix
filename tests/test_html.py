import schematix

TEST_DIR = "/".join(__file__.split("/")[:-1]) + "/"
FILENAME = 'test1.html'

FILENAME = TEST_DIR + FILENAME

f = open(FILENAME)
tables = list(schematix.import_html(f))

def test_filename_import():
    tables_from_filename = schematix.import_html(FILENAME)

def test_url_import():
    url = 'http://www.cfa.harvard.edu/castles/'
    url = 'http://www.asian-nation.org/population.shtml' 
    tables_from_url = list(schematix.import_html(url))
    #assert tables_from_url[1].get_header(0) == 'Ethnic Group'
    for t in tables_from_url:
        if t.is_relational:
            print
            t.show_text()
        else:
            print
            print t.is_relational
            t.show_text()

def test_metadata():
    assert len(tables) == 3
    assert tables[0].dim == (4,3)

def test_parsing_results():
    assert tables[0].get_header(2) == 'Salary'
    assert tables[0].get_cell_val(0,0) == 1
    assert tables[0].get_cell_display_val(0,0) == '1'
    assert tables[1].get_cell_val(1,1) == 7504.93
    assert tables[1].get_cell_display_val(1,1) == '7,504.93%'

if __name__ == '__main__':
    test_url_import()
    
    print tables[0].get_cell_val(0,0)
    print tables[0].get_cell_display_val(0,0)
    for t in tables:
        print
        t.show_text()
