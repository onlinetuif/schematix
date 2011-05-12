import logging
from xlrd import open_workbook, XLRDError
import sys

from schematix.parse_util import BaseTable, BaseCell

CELL_TYPE_LOOKUP = ['EMPTY', 'TEXT', 'NUMBER', 'DATE', 'BOOLEAN', 
                    'ERROR', 'BLANK']

MAX_ROWS_PER_SHEET = 10000

def load_spreadsheet(source):
    """Attempt to open the specified file using xlrd.  

    'source' should either be an absolute filename, or an open
    file object (e.g., the result of urllib.urlopen)
    
    Catches and suppresses common exceptions, but outputs a warning.
    """
    # TODO: use real python warnings
    try:
        if hasattr(source,'read'):
            workbook = open_workbook(file_contents=source.read(), 
                                     formatting_info=True,
                                     logfile=sys.stderr)
        else:
            workbook = open_workbook(source, 
                                     formatting_info=True,
                                     logfile=sys.stderr)
    except XLRDError, e:
        if 'Expected BOF' in str(e):
            logging.error("Error reading file (file extension may be wrong):")
            logging.error(e)
        elif 'Workbook is encrypted' in str(e):
            logging.error("Encrypted workbook:")
            logging.error(e)
        elif "Can't find workbook in OLE2" in str(e):
            logging.error("Weird OLE2 doc format:")
            logging.error(e)
        else:
            raise
        return
    except IOError, e:
        if 'Permission denied' in str(e):
            logging.error("Error reading XLS file (check file permissions):")
            logging.error(e)
        else:
            raise
        return
    except EnvironmentError, e:
        if 'Errno 22' in str(e):
            logging.error("Error reading XLS file (file may be empty):")
            logging.error(e)
        else:
            raise
        return
    return workbook

def parse_workbook(wb):
    # for each worksheet in the workbook,
    #   loop through all cells
    #   get text, value, fmt, style
    # Save in XLSTable object
    if not wb:
        return []
    xls_tables = []
    for i in range(wb.nsheets):
        t = XLSTable(wb, i)
        xls_tables.append(t)
    
    return xls_tables

class XLSTable(BaseTable):
    """Represents a data block in an XLS file"""

    def __init__(self, workbook, sheet_num):
        # for every cell in sheet, load cell attributes
        BaseTable.__init__(self)
        sheet = workbook.sheet_by_index(sheet_num)
        self.cells = [[] for _ in range(min(sheet.nrows, MAX_ROWS_PER_SHEET))]

        format_map_str = {}
        for k, v in workbook.format_map.iteritems():
            format_map_str[k] = v.format_str.encode('utf8')

        for rownum in range(min(sheet.nrows, MAX_ROWS_PER_SHEET)):
            for colnum in range(sheet.ncols):
                cell = sheet.cell(rownum, colnum)
                style = {}
                # get style and formatting attributes
                fmt = format_map_str[workbook.xf_list[cell.xf_index].format_key]

                data_type = CELL_TYPE_LOOKUP[cell.ctype]
                text = get_display_text(cell.value, data_type, fmt)
                self.cells[rownum].append(
                    XLSCell(text, cell.value, fmt, style, data_type))

        self.mark_merged_cells(sheet.merged_cells)
        BaseTable.clean(self)

    def mark_merged_cells(self, merged_cells):
        """ Mark merged cells, copy value from top-left cell to 
        others in merged area"""
        cells = self.cells
        for crange in merged_cells:
            rlo, rhi, clo, chi = crange
            for rowx in xrange(rlo, rhi):
                for colx in xrange(clo, chi):
                    cells[rowx][colx].merged = 'CHILD'
                    # TODO: copy cell from (rlo, clo) to (rowx, colx)
            cells[rlo][clo].merged = 'PARENT'
            cells[rlo][clo].merge_range = (rhi-rlo, chi-clo)

def get_display_text(value, data_type, fmt):
    if isinstance(value, basestring):
        try:
            value = float(value)
        except ValueError:
            return value

    text = str(value)
    if value is None:
        return text
    if fmt.endswith('_'):
        fmt = fmt[:-1]
    if (fmt in ['GENERAL',''] and
        data_type == 'NUMBER'):
        if value//1 == value:
            fmt = '0'
        elif value*10//1 == value*10:
            fmt = '0.0'
        elif value**100//1 == value*100:
            fmt = '0.00'
        else:
            fmt = '0'
        return (format_number(value, fmt) or text)
    elif fmt in ['0', '0.0', '0.00', '0.000', '#,##0', '#,##0.00']:
        return (format_number(value, fmt) or text)
    elif fmt.endswith('%'):
        return (format_number(value, fmt[:-1]) or text)
    elif fmt.startswith('"$"'):
        return (format_number(value, fmt[3:]) or text)

    return text

import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
# FIXME
# To make this more robust, we should actually parse the fmt string.
# Ideas:
# - First, split on ';' character, should be up to 4 sections:
#   pos/neg/zero/text
# - For appropriate section, parse format string
# - To parse, find the decimal separator.  Then proceed to the left, adding
#   appropriate characters to output at each position.  Then proceed to the
#   right, again adding appropriate characters at each position.
# - More info at: 
# http://svn.services.openoffice.org/opengrok/xref/Current%20%28trunk%29/svl/source/numbers/zformat.cxx
# - ImpGetNumberOutput, ImpGetDateOutput, ImpGetTimeOutput, etc
# - Fractional formatting (lines 2196-2459)
def format_number(value, fmt):
    # print 'value: %r, fmt: %r' % (value, fmt)
    try:
        if value == '':
            return ''
        elif fmt == '0':
            return '%d' % value
        elif fmt == '0.0':
            return '%.1f' % value
        elif fmt == '0.00':
            return '%.2f' % value
        elif fmt == '0.000':
            return '%.3f' % value
        elif fmt == '#,##0':
            return locale.format_string('%d', value, grouping=True)
        elif fmt == '#,##0.0':
            return locale.format_string('%.1f', value, grouping=True)
        elif fmt == '#,##0.00':
            return locale.format_string('%.2f', value, grouping=True)
        return None
    except ValueError:
        return None
    return None

class XLSCell(BaseCell):
    def __init__(self, text, value, fmt, style, data_type):
        BaseCell.__init__(self, text, value, data_type, fmt, style)
        self.merged = 'SINGLE'
