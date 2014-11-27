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

"""Cherry picking workflow"""

import copy, collections

import xlrd as X  ## dependency

import fileutil as F
import worklist as W
import plates

class IndexFileError( Exception ):
    pass

class BaseIndex(object):
    """
    Common base for Table (Excel) parsing.
    
    Assumes the following columns:
    * ID ... primary ID of construct
    * sub-ID ... optional secondary ID, e.g. for clone
    * plate ... plate ID (str or int)
    * pos ... position (str or int)
    * at least one additional column (number of columns used to identify header line)
    
    Empty columns (spacers without header name) are currently *not* supported.
    Rows without value in the first column are silently ignored. 
    
    ID + sub-ID (if any) are combined into a 'ID#sub-ID' index key for 
    the entry. If there is no sub-ID given, the ID is the key. ID and sub-ID
    are stripped and lower-cased internally so that upper and lower case
    versions are equally valid. 
    
    The content of each row is parsed into a dictionary {column-title:value,}
    which is then mapped to the index key (ID or ID#subID).
    
    The complete dictionary of each row can be accessed in two ways:
    
    >>> parser['BBa0010', 'a']
    {'plate':'sb01', 'position':'A2', 'id':'BBa0010', 'sub-id':'a'}
    
    or
    >>> parser['BBa0010#a']
    {'plate':'sb01', 'position':'A2', 'id':'BBa0010', 'sub-id':'a'}

    The original ID and sub-ID (not lower-cased) are available in this dict.

    or plate and position of a given entry can be accessed directly:
    >>> parser.position('BBa0010', 'a')
    ('sb10', 'A2')
    >>> parser.position('bba0010#a')
    ('sb10', 'A2')
        
    This base implementation assumes that every ID+sub-ID is assigned to
    exactly one plate and position.
    
    Additionally, the parser recognizes two different keywords in the first
    column of any row *before* the table header -- 'plate' and 'param':
    
    * plate  plate_ID  384   -- will assign 'plate_ID' to a 384 well format
    * plate  XY02      6     -- will assign plate 'XY02' to a 6 well format
    These values are stored in the BaseIndex._plates dictionary which is mapping
    plate IDs to plates.PlateFormat instances:
    >>> parser._plates['plate_ID'] = plates.PlateFormat(384)
    >>> parser._plates['XY02'] = plates.PlateFormat(6)
    
    Default for all plates is PlateFormat(96). This default value can be
    overridden in the constructor.

    The 'param' keyword signals generic key - value pairs that are put into
    ._params:

    * param    volume    130    ul
    ... is converted into 
    >>> parser._params['volume'] = 130
    """
    
    #: identify header row if first column has this value 
    HEADER_FIRST_VALUE = 'ID'

    _header0 = HEADER_FIRST_VALUE.lower()

    def __init__(self, plateformat=plates.PlateFormat(96),
                 relaxedId=True):
        """
        @param plateformat: plates.PlateFormat, default microplate format
        @param relaxedId: bool, fall back to matching by main ID only if sub-ID 
                          is not given, for example:
                              parts['Bba001'] may return parts['Bba001#a']
        """
        self._params = {}
        self._index = {}
        self._plates = {'default':plateformat}
        
        self.relaxedId = relaxedId

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
    
    def parsePlateformat(self, values):
        r = self.parseParam(values, keyword='format')
        if not r:
            return r
        
        plate = r.keys()[0]
        r[plate] = plates.PlateFormat(r[plate])
        
        return r
        

    def intfloat2int(self,x):
        """convert floats like 1.0, 100.0, etc. to int where applicable"""
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
    
    def cleanEntry(self, d):
        """convert and clean single part index dictionary (in place)"""
        for key, value in d.items():
            d[key] = self.clean2str(value)

    def parsePreHeader(self, values):
        r = self.parseParam(values)
        self._params.update(r)
        
        r = self.parsePlateformat(values)
        self._plates.update(r)

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
        
    def convertId(self, ids):
        """
        Normalize input ID or ID + sub-ID tuple into single lower case string.
        @param ids: float or int or str or unicode or [float|int|str|unicode]
        @return unicode, 'ID#subID' or 'ID'
        """
        if not type(ids) in [list, tuple]:
            ids = [ids]
        
        ids = [unicode(self.intfloat2int(x)).lower().strip() for x in ids]
        ids = [ x for x in ids if x ]  ## filter out empty strings but not '0'
        if len(ids) > 1:
            return '#'.join(ids)
        return ids[0]
    
    def detectHeader(self, values):
        if values and unicode(values[0]).lower().strip() == self._header0:
            return True
        return False
    

    def readExcel(self, fname):
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
            ## iterate until there is a row with at least 5 non-empty values
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

        except IndexError, why:
            raise IndexError, 'Invalid Index file (could not find header).'
    

    def addEntry(self, d):
        """
        Add new entry to index.
        @param d: dict, {'id':str|int, 'sub-id':str|int, ... }
        """
        part_id = self.convertId( (d['id'], d.get('sub-id', '')) )
        self._index[ part_id ] = d
    
    def __getitem__(self, item):
        """
        PartIndex[partID] -> [ {'plate':str, 'pos':str, 'barcode':str } ]
        @raise KeyError, if given ID doesn't match any registered part
        """
        try:
            id = self.convertId(item)
            return self._index[id]
        except KeyError:
            if self.relaxedId:
                for key, value in self._index.items():
                    if key.split('#')[0] == id:
                        return value
                raise
    
    def __len__(self):
        """len(PickList) -> int, number of samples to pick"""
        return len(self._index)
    
    def keys(self):
        return self._index.keys()
    
    def values(self):
        return self._index.values()
    
    def items(self):
        return self._index.items()

    def position(self, id, subid='', default=None):
        """
        Return plate and position of (arbitrary) first match to given 
        ID, and, if given, plate.
        @param id [, subid]: str, ID and optional sub-ID
        @default: optional default return value
        @return: (str,str), tuple of (plateID, position)
        """
        id = self.convertId((id, subid))
        
        if default is not None and not id in self._index:
            return default

        r = self[id]
        return r['plate'], r['pos']
    
    def plateFormat(self, plate=''):
        return self._plates.get(plate, self._plates['default'])


class PartIndex(BaseIndex):
    """
    Parse and access a table that maps part-IDs to source locations.
    
    PartIndex extends the BaseIndex class by allowing multiple locations
    per part. The low level return value of the index thus always is a list
    of dictionaries rather than a single dictionary.
    
    The position() method can be restricted to only match positions in a 
    given plate and will return the first position found (if any).
    
    The filterByPlate() method returns a new PartIndex containing only 
    entries from a given plate.
    """
    
    def addEntry(self, d):
        """
        Add new entry to part index.
        @param d: dict, {'id':str|int, 'sub-id':str|int, plate':str|int, 
                         'position':str|int, 'barcode':str|int }
        """
        part_id = self.convertId((d['id'], d['sub-id']))

        if not part_id in self._index:
            self._index[part_id] = []

        self._index[ part_id ] += [ d ]

    
    def __len__(self):
        """len(partindex) -> int, number of registered positions"""
        return sum( [ len(i) for i in self._index.values() ] )
    
    def position(self, id, subid='', plate=None, default=None):
        """
        Return plate and position of (arbitrary) first match to given 
        ID, and, if given, plate.
        @param id [, subid]: str, ID and optional sub-ID
        @param plate: str or [str], optional plate ID or several plate IDs
        @default: optional default return value
        @return: (str,str), tuple of (plateID, position)
        """
        id = self.convertId((id, subid))
        
        if default is not None and not id in self._index:
            return default

        r = self[id]

        if plate:
            if not type(plate) in [list, tuple]:
                plate = [plate]
            plate = [self.clean2str(x) for x in plate]
           
            for d in r:
                if d['plate'] in plate:
                    return d['plate'], d['pos']
            
            if default:
                return default

            raise KeyError, 'no entry found for ID %s in plate(s) %r' % \
                  (id, plate)
        
        return r[0]['plate'], r[0]['pos']
    
    def filterByPlate(self, plateID):
        """
        @return PartIndex, sub-index of all partIDs assigned to given plate
        """
        plateID = self.clean2str(plateID)
        
        r = {}
        for key, entries in self._index.items():
            entries = [ e for e in entries if e['plate'] == plateID ]
            if entries:
                r[key] = entries
            
        p = PartIndex()
        p._index = r
        p._params = copy.copy(self._params)
        
        return p
    
    
class TargetIndex(BaseIndex):
    """
    Index extension for a target table mapping constructs with a certain
    ID to a target position.

    Assumes the following columns:

    * ID ... target ID of new well/reaction
    * sub-ID ... optional secondary ID (ID#sub-ID must be unique in table)
    * plate ... target plate ID (str or int)
    * pos ... target position (str or int) within target plate

    * one or more "source" columns holding IDs of source constructs that
      should be pipetted into target. Default column title is "source", can
      be adapted in __init__
      
    Assumes volume definition for each source before the table header:
        volume    <source column>  <volume>
    Example:
        volume    template    5
    Declares that 5 ul should be transferred from sources given in column 
    "template".
    """

    def __init__(self, srccolumns=['source'], volume=None ):
        """
        
        @param srccolumns: [str] | [(str,str),str], list of column headers
        """
        super(TargetIndex, self).__init__()  
        self._index = collections.OrderedDict()  ## replace unordered dict
        
        self.source_cols = self._clean_headers(srccolumns)
        self._volume = {'default':volume}

    def _clean_headers(self, values):
        r = []
        for v in values:
            if type(v) in [list, tuple]:
                r += [ self._clean_headers(v) ]
            else:
                r += [ unicode(v).lower().strip() ]
        return r
    
    def parsePreHeader(self, values):
        super(TargetIndex,self).parsePreHeader(values)
        
        r = self.parseParam(values, keyword='volume')
        if r and not r.keys()[0] in self.source_cols + ['default']:
            raise IndexFileError, \
                  'volume definition "%s" does not match any source column' %\
                  r.keys()[0]

        self._volume.update(r)
    
    def volume(self, srcol, default=None):
        """
        @param srcol - str, source column name
        @param default - int | float, default volume if none registered for
                         given column AND if there is no default volume for
                         the table.
        @return int | float | None, volume registered for given source column
        """
        return self._volume.get(srcol, self._volume['default']) or default
    
   
class CherryWorklist(object):
    """
    Usage:
    >>> targets = TargetIndex()
    >>> targets.readExcel('pcr_reactions.xls')
    >>>
    >>> parts = PartIndex()
    >>> parts.readExcel('templates.xls')
    >>> parts.readExcel('primers.xls')
    >>>
    >>> cwl = CherryWorklist('worklist.gwl', targets, parts)
    >>> cwl.toWorklist(volume=5, byLabel=True)
    >>> cwl.close()
    
    This will read in three Excel files -- one containing a definition of
    new reactions / wells to create or cherry pick to, the other two containing
    the location of all the templates and primers references in the first one.
    
    cwl.toWorklist() will populate the worklist text file with aspirate/dispense
    statements that transfer liquid from source wells to target wells. The plate
    IDs used in the input tables can either be interpreted as barcodes/IDs 
    (byLabel=False which is the default) or they will be interpreted as 
    labware labels (byLabel=True).
    
    The volume to be transferred can be specified for each source column within
    the target Excel table (see TargetIndex).
    """
    
    def __init__(self, fout, targetIndex, sourceIndex, reportErrors=False):
        self.iTargets = targetIndex
        self.iParts = sourceIndex
        self.iProcessed = TargetIndex()
        self.wl = W.Worklist(fout, reportErrors=reportErrors)
        
    def close(self):
        """close the internal worklist file handle"""
        self.wl.close()
    
    def toWorklist(self, srccolumns=[], volume=None, byLabel=False):
        """
        @param srccolumns - [str], source columns to be processed [all]
        @param volume - int, transfer volume if none is specified in table [None]
        @param byLabel - bool, use labware labels as IDs rather than 
                         ID/barcode [False]
        """
        srccolumns = [s.strip() for s in srccolumns] or self.iTargets.source_cols
        
        for col in srccolumns:
            V = self.iTargets.volume(col, volume)
            
            for target, d in self.iTargets.items():
                
                try:
                    dst_plate, dst_pos = self.iTargets.position(target)
                    
                    if type(col) in [tuple,list]:
                        src_id = [d[s] for s in col]
                    src_id = d[col]
                    
                    if src_id:
                        
                        src_plate, src_pos = self.iParts.position(src_id)
                        
                        dst_format = self.iTargets.plateFormat(dst_plate)
                        src_format = self.iParts.plateFormat(src_plate)
                        
                        dst_pos = dst_format.pos2int(dst_pos)
                        src_pos = src_format.pos2int(src_pos)
                        
                        self.wl.transfer(src_plate, src_pos, dst_plate, dst_pos, 
                                         V, byLabel=byLabel)
                except plates.PlateError, why:
                    raise IndexFileError, \
                          'Error processing target record "%s":\n%s' \
                          % (target, why) 
        
    
    
######################
### Module testing ###
import testing, tempfile

class Test(testing.AutoTest):
    """Test PlateFormat"""

    TAGS = [ testing.NORMAL ]

    def prepare(self):
        self.f_parts = F.testRoot('partslist.xls')
        self.f_simple = F.testRoot('targetlist.xls')
        self.f_pcr = F.testRoot('targetlist_PCR.xls')
        
        self.f_worklist = tempfile.mktemp(suffix=".gwl", prefix="worklist_")
    
    def cleanUp(self):
        if not self.DEBUG:
            F.tryRemove(self.f_worklist)
        
    def test_partIndex(self):
        self.p = PartIndex()
        self.p.readExcel(self.f_parts)

        self.assertEqual(self.p['sb0101',2], self.p['sb0101#2'])
        self.assertEqual(len(self.p['sb0111']), 2)
        
        self.assertEqual(len(self.p), 27)

        self.assertEqual(self.p.position('sb0102', '2'), (u'SB10', u'A5'))
        
        self.assertEqual(self.p.position('sb0102#2', plate='SB10'), 
                         self.p.position('sb0102', '2'))
        
        self.assertEqual(self.p._plates['SB11'], plates.PlateFormat(384))

    def test_targetIndex_simple(self):
        t = TargetIndex(sourceColumns=[('construct','clone')])
        t.readExcel(self.f_simple)
    
    def test_targetIndex_multiple(self):
        t = TargetIndex(sourceColumns=['template','primer1','primer2'])
        t.readExcel(self.f_pcr)
        
        self.assertTrue(t._volume['template'] == 2)
        self.assertEqual(t._volume['primer1'], 5)
        self.assertEqual(t._volume['primer2'], 5)
    
    def test_generate_worklist_v0(self):
        parts = PartIndex()
        parts.readExcel(self.f_parts)
        
        t = TargetIndex(sourceColumns=['template','primer1','primer2'])
        t.readExcel(self.f_pcr)
        
        t.toWorklist(self.f_worklist, parts, byLabel=True)
    
    def test_generate_worklist(self):
        parts = PartIndex()
        parts.readExcel(self.f_parts)
        
        t = TargetIndex(sourceColumns=['template','primer1','primer2'])
        t.readExcel(self.f_pcr)
        
        cwl = CherryWorklist(self.f_worklist, t, parts)
        
        cwl.toWorklist(byLabel=True, volume=10)
        
        cwl.close()
    

