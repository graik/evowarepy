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

from evoware import PlateFormat, PlateError

class SampleIndex(object):
    """
    Extension of the basic Excel reader that is building an index of sample
    locations mapped to a sample ID.
    
    Assumes the following columns in the Excel table:
    * ID ... primary ID of construct
    * sub-ID ... optional secondary ID, e.g. for clone/copy of same construct
    * plate ... plate ID (str or int)
    * pos ... position (str or int)
    
    The order of these columns may be changed but HEADER_FIRST_VALUE then needs
    to be adapted.
    
    ID + sub-ID (if any) are combined into a 'ID#sub-ID' index key for each
    row / entry. If there is no sub-ID given, the ID is the key. ID and
    sub-ID are stripped and lower-cased internally so that upper and lower
    case versions are equally valid.
    
    Parser limitations
    ===================
    
    As before, rows without value in the first column are silently ignored. 
    Empty header columns (spacers without header name) are *not*
    supported. A workaround is to give spacer columns a one-character header
    such as '-' or '.'.
    
    Plate format handling
    ======================
    
    Beyond the "param" keyword, the parser recognizes 'plate' as a special
    keyword in the first column of any row *before* the table header.
    Examples:
    
    plate  plate_ID  384   -- will assign 'plate_ID' to a 384 well format
    plate  XY02      6     -- will assign plate 'XY02' to a 6 well format
    
    These values are stored in the BaseIndex._plates dictionary which is mapping
    plate IDs to plates.PlateFormat instances:
    >>> parser._plates['plate_ID'] = plates.PlateFormat(384)
    >>> parser._plates['XY02'] = plates.PlateFormat(6)
    
    Default for all plates is PlateFormat(96). This default value can be
    overridden in the constructor.
    """
    
    def __init__(self, plateformat=PlateFormat(96), relaxedId=True):
        """
        @param plateformat: plates.PlateFormat, default microplate format
        @param relaxedId: bool, fall back to matching by main ID only if sub-ID 
                          is not given, for example:
                              parts['Bba001'] may return parts['Bba001#a']
        """
        self._index = {}
        self._plates = {'default':plateformat}
        
        self.relaxedId = relaxedId
