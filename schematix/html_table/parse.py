"""Module for scoring and classifying rows of HTML tables"""

from StringIO import StringIO
from urllib2 import urlopen
from copy import deepcopy

import logging

from premailer import Premailer
from lxml import etree

from schematix.parse_util import BaseTable, BaseCell

import cgi
def log(text):
    logging.debug(cgi.escape(unicode(text)).encode('ascii','xmlcharrefreplace'))

def get_row_attributes(tr):
    """Returns row-specific attributes of an lxml tr element"""
    row_group = tr.getparent().tag
    if row_group == 'table':
        style = get_attributes(tr)
    else:
        style = {'row_group':row_group}
        style.update(get_attributes(tr))
    return style

def get_cell_attributes(td):
    """Returns cell-specific attributes of an lxml tr or td element"""
    style = {}
    style.update(get_attributes(td))
    cur_el = td
    while len(list(cur_el.iterchildren())) == 1:
        cur_el = list(cur_el.iterchildren())[0]
        t = str(cur_el.tag)
        if t in ('b','strong'):
            style['font-weight'] = 'bold'
        elif t in ('i','em'):
            style['font-style'] = 'italic'
        elif t in ('center'):
            style['text-align'] = 'center'
        elif t in ('font'):
            if cur_el.attrib.get('color'):
                style['color'] = cur_el.attrib.get('color')
            if cur_el.attrib.get('face'):
                style['face'] = cur_el.attrib.get('face')
            if cur_el.attrib.get('size'):
                style['font-size'] = cur_el.attrib.get('size')
        elif t in ('img'):
            style['image'] = 'image'
        elif t in ('a'):
            style['link'] = 'link'
        style.update(get_attributes(cur_el))

    return style

def get_attributes(element):
    style = {}

    # Add attributes from element attributes
    element_attr_list = {'align':'text-align',
                         'bgcolor':'background-color',
                         'colspan':'colspan',
                         'rowspan':'rowspan'}
    for k, v in element.attrib.iteritems():
        if k in element_attr_list:
            style[element_attr_list[k]] = v

    style_attr_list = ['background-color',
                       'color',
                       'font-family',
                       'font-size',
                       'font-style',
                       'font-weight',
                       'text-align',
                       'text-decoration']
    style_attrs = element.attrib.get('style','')
    try:
        for k, v in [x.strip().split(':', 1)
                    for x in style_attrs.split(';') if ':' in x.strip()]:
            if k in style_attr_list:
                style[k] = v
    except ValueError:
        print 'ValueError'

    return style

def load_html(source):
    """Return string of HTML from source

    source should be an absolute filename, url, or an open file object (e.g.,
    the result of urllib.urlopen)
    """
    # TODO: can you remove this? (seems to be repeated in core.py)
    if isinstance(source, basestring):
        if source.startswith('http://'):
            source = urlopen(source)
        else:
            source = open(source)

    return source.read()

import urlparse
def get_external_css(html, base_url):
    print 'base_url: %s' % base_url
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(html), parser)

    find_all_links = etree.XPath('//link')

    external_css = []
    for link in find_all_links(tree):
        link_type = link.attrib.get('type')
        link_href = link.attrib.get('href')
        if link_type == 'text/css' and link_href.endswith('.css'):
            external_css.append(urlparse.urljoin(base_url, link_href))
    
    return external_css

def put_css_inline(html, base_url):
    external_styles = []
    try:
        #external_styles = get_external_css(html, base_url)
        pass
    except UnicodeDecodeError:
        print 'UnicodeDecodeError'
    except IOError:
        print 'IOError'
    import lxml.cssselect
    try:
        p = Premailer(html, base_url=base_url,
                      external_styles=external_styles)
        return p.transform()
    except AssertionError:
        return html
    except lxml.etree.XMLSyntaxError:
        return html
    except lxml.etree.SerialisationError:
        return html
    except AttributeError:
        return html
    except lxml.cssselect.SelectorSyntaxError:
        return html

def parse_page(html):
    """Extracts table and cell information from html page.
    
    HTML tables are extracted and returned as a list of HTMLTable objects,
    consisting of HTMLCell objects."""

    # convert html string to etree form
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(html), parser)

    find_all_tables = etree.XPath('//table')
    find_rows = etree.XPath('tr|thead/tr|tfoot/tr|tbody/tr')
    find_cells = etree.XPath('td|th')

    # initialize html_tables list
    html_tables = []
    for table in find_all_tables(tree):
        cells = [[] for _ in find_rows(table)]
        h = HTMLTable(cells)
        html_tables.append(h)

    # traverse html tree to find tables, rows, cells
    for i, table in enumerate(find_all_tables(tree)):
        cells = html_tables[i].cells
        for j, tr in enumerate(find_rows(table)):
            row_style = get_row_attributes(tr)
            for td in find_cells(tr):
                cell_style = dict(row_style)
                cell_style.update(get_cell_attributes(td))
                tag = td.tag
                text = etree.tostring(td, method='text', with_tail=False,
                                      encoding=unicode).strip()
                value, fmt = get_real_value(text)
                c = HTMLCell(text, value, fmt, tag, cell_style)
                cells[j].append(c)

    # process merged cells
    for table in html_tables:
        table.unpack_merged_cells()

    # remove empty cols and rows
    table.clean()

    return html_tables

class HTMLTable(BaseTable):

    def __init__(self, cells):
        BaseTable.__init__(self)
        self.cells = cells

    def unpack_merged_cells(self):
        for row in self.cells:
            for cell in row:
                if (cell.style.get('colspan') or
                    cell.style.get('rowspan')):
                    cell.merged = 'PARENT'
                    cell.mergespan = (int(cell.style.get('colspan','1')),
                                      int(cell.style.get('rowspan','1')))

        for rownum, row in enumerate(self.cells):
            # create new_row with colspan cells expanded
            new_row = []
            for colnum, cell in enumerate(row):
                new_row.append(cell)
                try:
                    colspan = int(cell.style.get('colspan'))
                    log('found colspan: %d' % colspan)
                except TypeError:
                    colspan = None 
                if colspan:
                    new_cell = deepcopy(cell)
                    new_cell.merged = 'CHILD'
                    for i in range(colspan - 1):
                        new_row.append(deepcopy(new_cell))
            self.cells[rownum] = new_row
        # propogate cells with rowspan downward
        for rownum, row in enumerate(self.cells):
            for colnum, cell in enumerate(row):
                try:
                    rowspan = int(cell.style.get('rowspan'))
                    log('found rowspan: %d (%s)' % (rowspan, cell.text))
                except TypeError:
                    rowspan = None
                if rowspan:
                    for i in range(rownum + 1, rownum + rowspan):
                        new_cell = deepcopy(cell)
                        new_cell.merged = 'CHILD'
                        new_cell.style['rowspan'] = None
                        self.cells[i].insert(colnum, new_cell)
        #for row in self.cells:
        #    log(('merged:',[cell.merged for cell in row]))

class HTMLCell(BaseCell):
    def __init__(self, text, value, fmt, tag, style):
        print 'self.fmt: %r' % fmt
        # TODO: make this more robust
        if isinstance(value, basestring):
            data_type = 'TEXT'
        else:
            data_type = 'NUMBER'
        BaseCell.__init__(self, text, value, data_type, fmt, style)
        self.tag = tag
        self.merged = 'SINGLE'

    #def is_empty(self):
    #    return (len(self.text) == 0 and not self.value)

    def __repr__(self):
        return self.text[:60].encode('ascii','ignore')

import locale
locale.setlocale(locale.LC_ALL,'')
def get_real_value(text):
    try:
        val = locale.atof(text.strip())
        return (val, 'GENERAL')
    except ValueError:
        pass

    try:
        val = locale.atof(text.strip().lstrip('$'))
        return (val, '$')
    except ValueError:
        pass

    try:
        val = locale.atof(text.strip().rstrip('%'))
        return (val, '%')
    except ValueError:
        pass

    return (text, None)

