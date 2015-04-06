##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 Raik Gruenberg
##
##   Licensed under the Apache License, Version 2.0 (the "License");
##   you may not use this file except in compliance with the License.
##   You may obtain a copy of the License at
##
##       http://www.apache.org/licenses/LICENSE-2.0
##
##   Unless required by applicable law or agreed to in writing, software
##   distributed under the License is distributed on an "AS IS" BASIS,
##   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##   See the License for the specific language governing permissions and
##   limitations under the License.
"""Base Parser for Excel tables"""

from evoware import fileutil as F

import xlrd as X  ## third party dependency

class ExcelFormatError(IndexError):
    pass

class XlsReader(object):
    """
    Common base for Table (Excel) parsing.
    
    A header row is identified according to HEADER_FIRST_VALUE (default:'ID'). 
    The content of each following row is then parsed into a dictionary 
    {column-title:value,} which is appended to the list `XlsReader.rows`.
    
    Arbitrary parameters can be defined before the header row using the 
    following syntax:
        param   <key>   <value>

    Example:
        param    volume    130    ul    
    ... which is converted into 
    >>> reader.params['volume'] = 130
    
    That means the "param" key word in the first colum signals a new parameter
    record, which will be added to the `params` dictionary of the reader.

    Empty header columns (spacers without header name) are currently *not*
    supported. A workaround is to give spacer columns a one-character header
    such as '-' or '.'.
    
    Rows without value in the first column are silently ignored. 
    
    Shortcuts are defined to make the reader behave more like a list:
    >>> reader.rows[0] == reader[0]
    >>> len(reader.rows) == len(reader)
    """
    
    #: identify header row if first column has this value 
    HEADER_FIRST_VALUE = 'ID'

    _header0 = HEADER_FIRST_VALUE.lower()

    def __init__(self):
        """
        """
        self.params = {}
        self.rows = []

    def intfloat2int(self,x):
        """convert floats like 1.0, 100.0, etc. to int *where applicable*"""
        if type(x) is float:
            if x % 1 == 0:
                x = int(x)
        return x

    def clean2str(self, x):
        """convert integer floats to int, then strip to unicode"""
        x = self.intfloat2int(x)

        if type(x) is not unicode:
            x = unicode(x)

        x = x.strip()
        return x

    def parseParam(self, values, keyword='param'):
        """
        Extract "param, key, value" parameter from one row of values 
        (collected before the actual table header).
        @return {key : value}, dict with one key:value pair or empty dict
        """
        if values:
            v0 = values[0]

            if v0 and type(v0) in (str,unicode) and v0.lower() == keyword:
                try:
                    key = unicode(values[1]).strip()
                    value = self.intfloat2int(values[2])
                    return {key: value}

                except Exception, error:
                    raise IndexFileError, 'cannot parse parameter: %r' % values

        return {}

    def parsePreHeader(self, values):
        r = self.parseParam(values)
        self.params.update(r)

    def detectHeader(self, values):
        if values and unicode(values[0]).lower().strip() == self._header0:
            return True
        return False

    def parseHeader(self, values):
        """
        @param values: [any], list of row values from input parser
        @return [unicode], list of table headers, lower case and stripped
        @raise IndexFileError, if "construct" is missing from headers
        """
        r = [ unicode(x).lower().strip() for x in values ]
        if not 'id' in r:
            raise IndexFileError, 'cannot parse table header %r' % values

        return r

    def read(self, fname):
        """
        @param fname: str, excel file name including path
        @raise IOError, if file cannot be found (presumably)
        @raise IndexFileError, if header row cannot be found or interpreted
        """
        book = X.open_workbook( F.absfile(fname) )
        sheet = book.sheets()[0]

        try:
            row = 0
            values = []
            ## iterate until there is a row starting with HEADER_FIRST_VALUE
            ## capture any "param, <key>, <value>" entries until then
            while not self.detectHeader(values):
                values = [ v for v in sheet.row_values(row) if v ] 
                self.parsePreHeader(values)
                row += 1

            ## parse table "header"
            keys = self.parseHeader(values)

            i = 0
            for row in range(row, sheet.nrows):
                values = sheet.row_values(row) 

                ## ignore rows with empty first column
                if values[0]:
                    d = dict( zip( keys, values ) ) 
                    self.cleanEntry(d)
                    self.addEntry(d)
                    i += 1

            return i

        except ExcelFormatError, why:
            raise ExcelFormatError, 'Invalid Excel file (could not find header).'

    def addEntry(self, d):
        """
        Add new entry to index.
        @param d: dict, {'id':str|int, 'sub-id':str|int, ... }
        @raise DuplicateID, if ID of given record clashes with existing ID
        """
        self.rows  += [ d ]

    def cleanEntry(self, d):
        """convert and clean single part index dictionary (in place)"""
        for key, value in d.items():
            d[key] = self.clean2str(value)
    
    def __len__(self):
        """len(PickList) -> int, number of samples to pick"""
        return len(self.rows)
    
    def __getitem__(self, item):
        return self.rows[item]
    

######################
### Module testing ###
from evoware import testing
import tempfile

class Test(testing.AutoTest):
    """Test XlsReader"""

    TAGS = [ testing.NORMAL ]

    def prepare(self):
        """Called once"""
        self.f_parts = F.testRoot('partslist.xls')
        self.f_primers = F.testRoot('primers.xls')
        self.f_simple = F.testRoot('targetlist.xls')
        self.f_pcr = F.testRoot('targetlist_PCR.xls')

    def cleanUp(self):
        """Called after all tests"""
        if not self.DEBUG:
            pass
    
    def test_xlsreader(self):
        self.r = XlsReader()
        self.r.read(self.f_parts)
        
        self.assertEqual(self.r.params['setting1'], u'value1')
        self.assertEqual(self.r.params['setting2'], u'value2')
        self.assertEqual(len(self.r.rows), 27)
        self.assertEqual(len(self.r.rows[0].keys()), 4)
        self.assertDictEqual(self.r.rows[0], \
            {u'plate': u'SB10', u'id': u'sb0101', u'sub-id': u'2', 
             u'pos': u'A1'} )
