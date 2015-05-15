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
    
class SampleError(Exception):
    pass

class Sample(object):
    """Representation of a single well / sample"""
    
    def __init__(self, id=None, subid=None, plate='', pos=0, 
                 plateformat=PlateFormat(96), **kwargs):
        self._id = ''
        self._subid = ''
        self._plateid = ''
        self._plateformat = None
        self._pos = 0
        
        ## initialize properties using setter methods
        self.id = (id, subid)    
        self.plateformat = plateformat
        self.plateid = plate
        self.position = pos

    @property
    def plateid(self):
        """ID of plate or container holding this sample"""
        return self._plateid
    
    @plateid.setter
    def plateid(self, plate):
        if plate is None:
            plate = ''
        assert type(plate) is str
        self._plateid = plate.strip()
    
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
    
    position2D = property(fget=_getposHuman, doc="""str, read-only property.
    'human readable' version of the well position. E.g. 'A1', 'B2', 'H12', etc. 
    """)
    
    def _setplateformat(self, plateformat):
        assert isinstance(plateformat, PlateFormat)
        self._plateformat = plateformat
    def _getplateformat(self):
        return self._plateformat
    
    plateformat = property(_getplateformat, _setplateformat)
    

    def intfloat2int(self,x):
        """convert floats like 1.0, 100.0, etc. to int *where applicable*"""
        if type(x) is float:
            if x % 1 == 0:
                x = int(x)
        return x

    def _setid(self, ids):
        """
        Normalize input ID or (ID, sub-ID) tuple or ID#subID string into pair of
        main ID and optional sub-ID.
        @param ids: float or int or str or unicode or [float|int|str|unicode]
        """
        if type(ids) in [str, unicode] and '#' in ids:
            ids = ids.split('#')

        if type(ids) not in [tuple, list]:
            ids = (ids,)

        ids = [unicode(self.intfloat2int(x)).strip() for x in ids]
        ids = [ x for x in ids if x ]  ## filter out empty strings but not '0'
        
        self._id = ids[0] if len(ids) > 0 else ''
        self._subid = ids[1] if len(ids) > 1 else ''
        
    def _getid(self):
        return self._id
    
    def _getsubid(self):
        return self._subid
    def _setsubid(self, subid):
        self._subid = subid if subid else ''
    
    def _getfullid(self):
        if self._subid:
            return '#'.join((self._id, self._subid))
        return self._id
    
    id = property(fget=_getid, fset=_setid,
                  doc='main sample ID (without sub-ID); or empty str')
    subid = property(fget=_getsubid, fset=_setsubid, 
                     doc='sub-ID if any; otherwise empty str')
    fullid = property(fget=_getfullid, fset=_setid, 
                      doc='complete ID which can be either ID or ID#subID')


class SampleList(object):
    """
    """
    
    def __init__(self, plateformat=PlateFormat(96), relaxedId=True):
        """
        @param plateformat: plates.PlateFormat, default microplate format
        @param relaxedId: bool, fall back to matching by main ID only if sub-ID 
                          is not given, for example:
                              parts['Bba001'] may return parts['Bba001#a']
        """
        self.samples = []
        self.plateformats = {'default':plateformat}
        self.params = {}

    def clean2str(self, x):
        """convert integer floats to int (if applicable), then strip to unicode"""
        x = self.intfloat2int(x)

        if type(x) is not unicode:
            x = unicode(x)

        x = x.strip()
        return x

    def cleanEntry(self, d):
        """convert and clean single sample dictionary (in place)"""
        for key, value in d.items():
            d[key] = self.clean2str(value)


    def addraw(self, d):
        """create new entry from dictionary"""
        pass
        

######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test Sample"""

    TAGS = [ testing.NORMAL ]

    def test_sample(self):
        s = Sample(id='BBa1000', subid=1.0, plate='plateA', pos='A1')
        self.assertEqual(s.id, 'BBa1000')
        self.assertEqual(s.subid, '1')
        self.assertEqual(s.fullid, 'BBa1000#1')
        self.assertEqual(s.position, 1)
        self.assertEqual(s.plateid, 'plateA')
        self.assertEqual(s.position2D, 'A1')
        
        s.id = 'BBa2000'
        self.assertEqual(s.id, 'BBa2000')
        self.assertEqual(s.subid, '')
        self.assertEqual(s.fullid, 'BBa2000')
        
        s.id = 'BBa3000#a'
        self.assertEqual(s.id, 'BBa3000')
        self.assertEqual(s.subid, 'a')
        
        
