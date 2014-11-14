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

class IndexFileError( Exception ):
    pass

class BaseParser(object):
    """Common base for Table (Excel) parsing"""

    def __init__(self):
        self._params = {}

    def parseParam(self, values):
        """
        Extract "param, key, value" parameter from one row of values 
        (collected before the actual table header).
        @return {key : value}, dict with one key:value pair or empty dict
        """
        if values:
            v0 = values[0]
    
            if v0 and type(v0) in (str,unicode) and v0.lower() == 'param':
                try:
                    key = unicode(values[1]).strip()
                    value = self.intfloat2int(values[2])
                    return {key: value}
                
                except Exception, error:
                    raise IndexFileError, 'cannot parse parameter: %r' % values

        return {}
        
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


    def addEntry(self, d):
        """Commit cleaned-up entry dictionary to index (abstract)"""
        pass
    
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
        
    
    def readExcel(self, fname):
        """
        @param fname: str, excel file name including path
        @raise IOError, if file cannot be found (presumably)
        @raise IndexFileError, if header row cannot be found or interpreted
        """
        book = X.open_workbook( F.absfile(fname) )
        sheet = book.sheets()[0]
        
        row = 0
        values = []
        ## iterate until there is a row with at least 5 non-empty values
        ## capture any "param, <key>, <value>" entries until then
        while len(values) < 5:
            values = [ v for v in sheet.row_values(row) if v ] 
            r = self.parseParam(values)
            self._params.update(r)
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


class PartIndex(BaseParser):
    """Parse part index Excel table(s)"""
    
    def __init__(self):
        super(PartIndex, self).__init__()
        
        self._index = {}

        self._bc2plate = {}
        self._plate2bc = {}
        
     
    def addEntry(self, d):
        """
        Add new entry to part index.
        @param d: dict, {'id':str|int, 'sub-id':str|int, plate':str|int, 
                         'position':str|int, 'barcode':str|int }
        """
        part_id = d['id']
        if d['sub-id']:
            part_id += '#' + d['sub-id']

        part_id = part_id.lower()

        if not part_id in self._index:
            self._index[part_id] = []

        del d['id']
        del d['sub-id']
        
        if d['barcode'] and d['plate']:
            self._bc2plate[d['barcode']] = d['plate']
            self._plate2bc[d['plate']] = d['barcode']

        self._index[ part_id ] += [ d ]

    
    def __getitem__(self, item):
        """
        PartIndex[partID] -> [ {'plate':str, 'pos':str, 'barcode':str } ]
        @raise KeyError, if given ID doesn't match any registered part
        """
        if type(item) is tuple:
            item = [ unicode(x).strip() for x in item ]
            
            if item[1]:
                item = '#'.join(item)  ## join ID and sub-ID
            else:
                item = item[0]  ## but ignore empty sub-ID argument
        
        item = unicode(item).lower().strip()
        
        return self._index[item]
    
    def getPosition(self, id, subid='', plate=None, default=None):
        """
        Return plate and position of (arbitrary) first match to given 
        ID, and, if given, plate.
        @param id [, subid]: str, ID and optional sub-ID
        @param plate: str or [str], optional plate ID or several plate IDs
        @default: optional default return value
        @return: (str,str), tuple of (plateID, position)
        """

        try:
            r = self[id, subid]
        except KeyError:
            if default:
                return default
            raise

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
    
    def __len__(self):
        """len(partindex) -> int, number of registered positions"""
        return sum( [ len(i) for i in self._index.values() ] )
    
    def keys(self):
        return self._index.keys()
    
    def values(self):
        return self._index.values()
    
    def items(self):
        return self._index.items()

    def filterByPlate(self, plateID):
        """
        @return PartIndex, sub-index of all partIDs assigned to given plate
        """
        plateID = unicode(plateID).lower().strip()
        
        r = {}
        for key, entries in self._index.items():
            entries = [ e for e in entries if e['plate'] == plateID ]
            if entries:
                r[key] = entries
            
        p = PartIndex()
        p._index = r
        p._params = copy.copy(self._params)
        
        return p
    
    
class TargetIndex(BaseParser):
    """Parse cherry picking table(s)"""
    
    def __init__(self):
        super(TargetIndex, self).__init__()
        
        self._index = collections.OrderedDict()  ## replace unordered dict
    
    def convertId(self, ids):
        """
        Normalize input ID or ID / sub-ID tuple into single lower case string.
        @param ids: int or str or unicode or [int, str, unicode]
        @return unicode, ID#subID
        """
        if not type(ids) in [list, tuple]:
            ids = [ids]
        
        ids = [unicode(self.intfloat2int(x)).lower().strip() for x in ids]
        ids = [ x for x in ids if x ]  ## filter out empty strings but not '0'
        if len(ids) > 1:
            return '#'.join(ids)
        return ids[0]
    
    def addEntry(self, d):
        """
        Add new entry to part index.
        @param d: dict, {'id':str|int, 'sub-id':str|int, plate':str|int, 
                         'position':str|int, 'barcode':str|int }
        """
        part_id = self.convertId( (d['id'], d.get('sub-id', '')) )

        del d['id']
        del d['sub-id']
        
        self._index[ part_id ] = d
    
    def __getitem__(self, item):
        """
        PartIndex[partID] -> [ {'plate':str, 'pos':str, 'barcode':str } ]
        @raise KeyError, if given ID doesn't match any registered part
        """
        id = self.convertId(item)
        
        return self._index[id]
    

    def __len__(self):
        """len(PickList) -> int, number of samples to pick"""
        return len(self._index)
    
    def __iter__(self):
        """
        for x in PickList: -> 
           {'id':str, 
            'dstplate':str, 'dstpos':int}
        """
        pass

class Picker(object):
    """Convert input part index and cherry picking table into worklist"""
    
    def __init__(self, findex, fpicking, fout):
        self.parts = PartIndex(*findex)
        self.f_picking = fpicking
        self.f_out = fout
    
    
fname = F.testRoot('partslist.xls')
self = PartIndex()
self.readExcel(fname)

fname = F.testRoot('targetlist.xls')
t = TargetIndex()
t.readExcel(fname)

print "Done"

