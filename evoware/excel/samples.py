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

from xlsreader import XlsReader
import keywords as K

from evoware import PlateFormat, PlateError

class XlsSampleReader(XlsReader):
    HEADER_FIRST_VALUE = K.column_plate

class Sample(object):
    """Representation of a single well / sample"""
    
    def __init__(self, plate='', pos=0, plateformat=PlateFormat(96)):
        self._plateid = plateid
        self._plateformat = plateformat
        self._pos = self._plateformat.pos2int(pos)
    
    def _setpos(self, pos):
        self._pos = self._plateformat.pos2int(pos)
    def _getpos(self):
        return self._pos
    def _getposHuman(self):
        return self._plateformat.int2human(self._pos)
    
    position = property(fget=_getpos, fset=_setpos, 
                        doc="""int, well position of this sample within plate. 
    On a 96 well plate, numbers run row-wise from upper left (1 = A1) to 
    lower right (96 = H12). Position 8 would be H1, 9 would be B1 etc. The
    position can be assigned a number::
    >>> sample.position = 9
    or a more human readable coordinate::
    >>> sample.position = 'B1'
    Both will yield the same result::
    >>> sample.position
       9
    """)
    
    positionHuman = property(fget=_getposHuman, doc="""str, read-only property.
    'human readable' version of the well position. E.g. 'A1', 'B2', 'H12', etc. 
    """)
    
    def _setplateformat(self, plateformat):
        assert isinstance(plateformat, PlateFormat)
        self._plateformat = plateformat
    def _getplateformat(self):
        return self._plateformat
    
    plateformat = property(_getplateformat, _setplateformat)
    
    

class SampleList(object):
    """
    Extension of the basic Excel reader that is building a list of sample
    locations.
    
    Assumes the following "parameters" defined before the actual sample table:
    * reagent    <plate_ID>   <well>
    (example 1: reagent   PCR-A   A2
     example 2: reagent   PCR-A   2)
    Optional: one or more plate format statements:
    * format   <plate_ID>    <well number>
    (example: format    PCR-A   96)
    
    Assumes the following columns in the sample table:
    * plate ... plate ID (str or int)
    * pos ... position (str or int)
    Optional:
    * volume ... volume in ul (int)    
    
    The order of these columns may be changed but HEADER_FIRST_VALUE then needs
    to be adapted.
    
    Plate format statements are needed if well positions are given as 
    "coordinates" such as A1, B2, etc. They are not needed if positions are
    given as running (integer) numbers.
        
    Parser limitations
    ===================
    
    As before, rows without value in the first column are silently ignored. 
    Empty header columns (spacers without header name) are *not*
    supported. A workaround is to give spacer columns a one-character header
    such as '-' or '.'.    
    """
    
    def __init__(self, plateformat=PlateFormat(96), relaxedId=True):
        """
        @param plateformat: plates.PlateFormat, default microplate format
        @param relaxedId: bool, fall back to matching by main ID only if sub-ID 
                          is not given, for example:
                              parts['Bba001'] may return parts['Bba001#a']
        """
        self.samples = []
        self.plates = {'default':plateformat}
        self.params = {}
        
        self.plateformat = plateformat

    def getSampleReaderClass(self, fname):
        return XlsSampleReader
    
    def readSamples(self, fname):
        R = self.getSampleReaderClass(fname)
        reader = R(plateformat=self.plateformat)
        reader.read(fname)
        
        for d in reader.rows:
            pass
        