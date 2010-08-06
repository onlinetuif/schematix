"""The SchematiX Python module."""

from schematix.spreadsheet import SpreadsheetExtractor
from schematix.html_table import HtmlTableExtractor

def import_spreadsheet(source):
    """Returns relational table representation of a spreadsheet file."""
    extractor = SpreadsheetExtractor(source)
    extractor.extract_schemas()
    return extractor.get_tables()

def import_html(source):
    """Returns relational table representation of the HTML 
    tables in an HTML file."""
    extractor = HtmlTableExtractor(source)
    extractor.extract_schemas()
    return extractor.get_tables()
