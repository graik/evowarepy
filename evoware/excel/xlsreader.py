##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2019 Raik Gruenberg
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

import evoware as E
from evoware import fileutil as F
from evoware import PlateFormat, PlateError, Plate
import keywords as K

import xlrd as X  ## third party dependency

class ExcelFormatError(IndexError):
    pass

class XlsReader(object):
    """
    Low level Excel table parsing. XlsReader extracts rows into a list of
    dictionaries. Additional (table-wide) parameters are extracted from
    'param' and 'format' entries placed before the header row. A single
    XlsReader instance can parse more than one file -- additional rows will
    be simply appended and parameter dictionaries will be updated with each
    additional file. However, there are no consistency checks -- i.e. row
    dictionaries from the second file can have different keys than previous
    records.
    
    Table Format
    ============
    
    A header row is identified according to HEADER_FIRST_VALUE (default:'ID'). 
    The content of each following row is then parsed into a dictionary 
    {column-title:value,} which is appended to the list `XlsReader.rows`.
    
    Empty header columns (e.g. spacers without header name) are currently *not*
    supported. A workaround is to give spacer columns a one-character header
    such as '-' or '.'.
    
    Rows without value in the first column are silently ignored.
    Only the first sheet in a workbook is parsed (this could be easily changed).
    
    Parameters
    ==========
    
    Arbitrary parameters can be defined *before* the header row using the 
    following syntax:
        param   <key>   <value>

    Example:
        param    volume    130    ul    
    ... which is converted into 
    >>> reader.params['volume'] = 130
    
    The "param" key word in the first colum signals a new parameter
    record, which will be added to the `params` dictionary of the reader.
    
    Plate and Plate format definitions
    ==================================
    
    XlsReader accepts a PlateIndex instance which maps plate descriptions
    (evoware.Plate instances) to a given plate ID. Plate instances are
    important for downstream applications as they capture row:column
    dimensions (aka plate format) as well as 'rackType' strings (aka labware
    type, needed if using barcodes).

    The default PlateIndex is a package-wide singleton instance
    'evoware.plates'. 
    
    The 'format' keyword in the first column anywhere before the actual
    header row signals a special plate format parameter which leads to 
    the addition / overriding of a Plate record in the PlateIndex. 
    Usage:
        format    <plate ID>   <number wells>
    
    Example:
        format    assay0123    384
        format    dest01       96
        
    The above example results in:
    
    >>> evoware.plates['assay0123']
        <Plate assay0123 : (384 wells)>
    >>> evoware.plates['dest01']
        <Plate dest01 : (384 wells)>
    
    Note that 'assay0123' has been interpreted as 'rackLabel', which is the 
    default behaviour. Initialize XlsReader with the parameter 'byLabel=False'
    if plate IDs should be interpreted as barcode. In this case, new
    plate entries will also receive a default 'rackType' string which can 
    be modified in the XlsReader constructor.
    
    The method plateFormat() will return the default PlateFormat(96) *unless*
    another format has been specified for a given plate ID.:
    
    >>> reader.plateFormat('assay0123') == plates.PlateFormat(384)
    >>> reader.plateFormat('nonsense')  == plates.PlateFormat(96)
    >>> reader.plateFormat('') == plates.PlateFormat(96)
    
    General Usage
    =============
    
    >>> reader = XlsReader()
    >>> reader.read('samples.xls')
    >>> reader.rows[0]
        {u'plate': u'SB10', u'id': u'sb0101', u'pos': u'A1'}
    >>> reader.params['setting1']
        u'value1'
    >>> reader.plateFormat('dest01')
        <384 well PlateFormat>

    List-like behaviour
    ===================

    Shortcuts are defined to make the reader behave more like a list:
    >>> reader.rows[0] == reader[0]
    >>> len(reader.rows) == len(reader)
    
    Note: not the complete list interface is currently implemented.
    """
    
    #: identify header row if first column has this value 
    HEADER_FIRST_VALUE = 'ID'

    _header0 = HEADER_FIRST_VALUE.lower()

    def __init__(self, plateIndex=E.plates, byLabel=True,
                 defaultRackType='%i Well Microplate'):
        """
        @param plateIndex: PlateIndex instance, default: evoware.plates
        @param byLabel: bool, interpret plate IDs as rackLabel (True);
                        if False, all plate IDs are considered barcodes
        @param defaultRackType: str, labware type assigned to new plates,
                                if byLabel=False, see also Plate.__init__
        """
        self.params = {}
        self.rows = []
        
        self.plateindex = plateIndex
        self.byLabel = byLabel
        self.defaultRackType = defaultRackType

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

    def parseParam(self, values, keyword=K.param):
        """
        Extract "param, key, value" parameter from one row of values 
        (collected before the actual table header).
        @return {key : value}, dict with one key:value pair or empty dict
        @raise ExcelFormatError
        """
        if values:
            v0 = values[0]

            if v0 and isinstance(v0, basestring) and v0.lower() == keyword:
                try:
                    key = unicode(values[1]).strip()
                    value = self.intfloat2int(values[2])
                    return {key: value}

                except Exception, error:
                    raise ExcelFormatError, 'cannot parse parameter: %r' \
                          % values

        return {}
    
    def parseFormatParam(self, values, keyword=K.plateformat):
        if values:
            v0 = values[0]
    
            if v0 and isinstance(v0, basestring) and v0.lower() == keyword:
                try:
                    key = unicode(values[1]).strip()
                    r = {'ID':key, 'wells':values[2]}
                    if len(values) > 3:
                        r['racktype'] = unicode(values[3]).strip()
                    else:
                        r['racktype'] = None
                    return r
                except Exception, error:
                    raise ExcelFormatError, 'cannot parse format record: %r' \
                          % values
        return {}

    def parsePlateformat(self, values):
        """
        Extract special plate format parameter from header row starting
        with 'format'.
        @return {plateID : Plate}, or empty dict
        """
        r = self.parseFormatParam(values, keyword=K.plateformat)
        if not r:
            return r
        
        plateid = r['ID']
        
        if self.byLabel:
            kwargs = {'rackLabel':plateid,
                      'rackType': r['racktype'] or self.defaultRackType}
        else:
            kwargs = {'barcode':plateid, 
                      'rackType': r['racktype'] or self.defaultRackType}
        
        plate = Plate(format=PlateFormat(r['wells']), **kwargs)
            
        return {plateid: plate}
    

    def parsePreHeader(self, values):
        r = self.parseParam(values)
        self.params.update(r)
        
        r = self.parsePlateformat(values)
        self.plateindex.update(r)

    def detectHeader(self, values):
        if values and unicode(values[0]).lower().strip() == self._header0:
            return True
        return False

    def parseHeader(self, values):
        """
        @param values: [any], list of row values from input parser
        @return [unicode], list of table headers, lower case and stripped
        @raise ExcelFormatError, if "construct" is missing from headers
        """
        r = [ unicode(x).lower().strip() for x in values ]
        if not self._header0 in r:
            raise ExcelFormatError, 'cannot parse table header %r' % values

        return r

    def read(self, fname):
        """
        Append data from given Excel file to internal list of rows and
        dictionary of parameters.
        @param fname: str, excel file name including path
        @raise IOError, if file cannot be found (presumably)
        @raise ExcelFormatError, if header row cannot be found or interpreted
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
        Add new row entry to list.
        @param d: dict, dictionary representing one row
        """
        self.rows  += [ d ]

    def cleanEntry(self, d):
        """convert and clean single row dictionary (in place)"""
        for key, value in d.items():
            d[key] = self.clean2str(value)
    
    def plateFormat(self, plate='', default=PlateFormat(96)):
        """
        @param plate: str, plate ID (or '')
        @return PlateFormat, plate format assigned to given plate ID
        """
        return self.plateindex.getformat(plate, default=default)

    def __len__(self):
        """len(reader) -> int, number of rows"""
        return len(self.rows)
    
    def __getitem__(self, item):
        """reader[int] -> dict, shortcut to dictionary of given row"""
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
        self.f_distribute = F.testRoot('distribution.xls')

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
        
        self.assertEqual(self.r.plateFormat('SB11'), PlateFormat(384))
        self.assertEqual(self.r.plateFormat(''), PlateFormat(96))
        
    def test_xlsreader_barcode(self):
        self.r2 = XlsReader(byLabel=False)
        self.r2.read(self.f_parts)
        
        self.assertEqual(E.plates['SB11'].rackType, '384 Well Microplate')
        self.assertEqual(E.plates['SB11'].barcode, 'SB11')

    def test_customFormat(self):
        self.r3 = XlsReader()
        self.r3.read(self.f_distribute)
        
        self.assertEqual(E.plates['reservoirA'].rackType, 'Trough 100ml')
        
