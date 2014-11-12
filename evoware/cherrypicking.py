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

import copy

import xlrd as X  ## dependency

import fileutil as F
import worklist as W

class IndexFileError( Exception ):
    pass

class PickerException( Exception ):
    pass

class PartIndex(object):
    """Parse part index Excel table(s)"""
    
    def __init__(self):
        self._index = {}
        self._params = {}

        self._bc2plate = {}
        self._plate2bc = {}
 
    def _parseParam(self, values):
        """Extract key : value parameter from one row of values"""
        if values:
            v0 = values[0]
    
            if v0 and type(v0) in (str,unicode) and v0.lower() == 'param':
                try:
                    key = unicode(values[1])
                    value = self._intfloat2int(values[2])
                    return {key: value}
                
                except Exception, error:
                    raise IndexFileError, 'cannot parse parameter: %r' % values

        return {}
        
    def _intfloat2int(self,x):
        """convert floats like 1.0, 100.0, etc. to int where applicable"""
        if type(x) is float:
            if x % 1 == 0:
                x = int(x)
        return x

    def _cleanId(self, x):
        """convert integer floats to int, then lower case and strip to unicode"""
        x = self._intfloat2int(x)
        
        if type(x) is not unicode:
            x = unicode(x)
        
        x = x.lower().strip()
        return x
    
    def cleanEntry(self, d):
        """convert and clean single part index dictionary"""
        for key, value in d.items():
            d[key] = self._cleanId(value)
        
    
    def addEntry(self, d):
        """
        Add new entry to part index.
        @param d: dict, {'construct':str|int, 'clone':str|int, plate':str|int, 
                         'position':str|int, 'barcode':str|int }
        """
        part_id = d['construct']
        if d['clone']:
            part_id += '#' + d['clone']

        if not part_id in self._index:
            self._index[part_id] = []

        del d['construct']
        del d['clone']
        
        if d['barcode'] and d['plate']:
            self._bc2plate[d['barcode']] = d['plate']
            self._plate2bc[d['plate']] = d['barcode']

        self._index[ part_id ] += [ d ]
        

    def parseExcel(self, fname):
        """
        @param fname: str, excel file name including path
        @raise IOError, if file cannot be found (presumably)
        """
        book = X.open_workbook( F.absfile(fname) )
        sheet = book.sheets()[0]
        
        row = 0
        values = []
        ## iterate until there is a row with at least 5 non-empty values
        ## capture any "param, <key>, <value>" entries until then
        while len(values) < 5:
            values = [ v for v in sheet.row_values(row) if v ] 
            r = self._parseParam(values)
            self._params.update(r)
            row += 1
        
        ## parse table "header"
        keys = [ unicode(x).lower().strip() for x in values ]
        if not 'construct' in keys:
            raise IndexFileError, 'cannot parse table header %r' % values
        
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
    
    def __getitem__(self, item):
        """
        PartIndex[partID] -> [ {'plate':str, 'pos':int|str, 'barcode':str } ]
        @raise KeyError, if given ID doesn't match any registered part
        """
        if type(item) is tuple:
            item = [ unicode(x).lower().strip() for x in item ]
            
            if item[1]:
                item = '#'.join(item)  ## join ID and sub-ID
            else:
                item = item[0]  ## but ignore empty sub-ID argument
        else:
            item = unicode(item).lower().strip()
        
        return self._index[item]
    
    def __len__(self):
        """len(partindex) -> int, number of registered parts"""
        return len(self._index)
    
    def keys(self):
        return self._index.keys()
    
    def values(self):
        return self._index.values()
    
    def items(self):
        return self._index.items()

    def plates(self):
        """plates() -> [str], list of plate IDs"""
        pass
    
    def filterByPlate(self, plateID):
        """
        by_plate(plateID) -> PartIndex, sub-index of all partIDs from plate
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
    
    
class PickList(object):
    """Parse cherry picking table(s)"""
    
    def __init__(self, f_picklist, volume):
        self.f_input = f_picklist
        self.volume = volume
    
    def __len__(self):
        """len(PickList) -> int, number of samples to pick"""
        pass
    
    def __iter__(self):
        """
        for x in PickList: -> 
           {'srcplate':str, 'srcpos':int, 
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
self.parseExcel(fname)

print "Done"

