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

import excel.keywords as K

import evoware as E
from evoware import PlateFormat, PlateError, Plate

class SampleError(Exception):
    pass

def intfloat2int(x):
    """convert floats like 1.0, 100.0, etc. to int *where applicable*"""
    if type(x) is float and x % 1 == 0:
        return int(x)
    return x

class Sample(object):
    """
    Representation of a single well / sample
    
    Properties:
    
    * id - str, main sample ID 
    * subid - str, secondary ID to, e.g., distinguish replicas and clones
    * fullid - str, (readonly) gives id#subid if there is a subid, else just id.
    
    * plate - a evoware.Plate instance
    * plateformat - shortcut to the plate's PlateFormat (row:column dimensions)
    * plateid - shortcut to plate.rackLabel *or* plate.barcode
    
    * position - int, well position, e.g. number 1 to 96
    * position2D - str, human readable well position (e.g. 'A1')
    A new position can be assigned to position either as number or 2D string.
    
    Usage:
    
    >>> s = Sample('BBa1000#a', plate=Plate('plateA'), pos='B1')
    is the same as:
    >>> s = Sample('BBa1000', 'a', Plate('plateA'), 9)
    and results in:
    >>> s.id
       'BBa1000'
    >>> s.subid
       'a'
    >>> s.fullid
       'BBa1000#a'
    >>> s.plateformat
       PlateFormat(96)
    >>> s.plateid
       'plateA'
    
    Arbitrary additional fields can be given as keyword arguments to the
    constructor:
    >>> s = Sample('BBa2000#1', plate=Plate('plateB'), pos=1, temperature=25)
    results in an additional 'temperature' field:
    >>> s.temperature
        25
    
    """
    
    ##__hash__ = None
    
    def __init__(self, id=None, subid=None, plate=None, pos=0,
                 **kwargs):
        self._id = ''
        self._subid = ''
        
        self._plate = plate or Plate()
        assert isinstance(self._plate, Plate)
        
        self._pos = 0
        
        ## initialize properties using setter methods
        if subid:
            self.id = (id, subid)
        else:
            self.id = id   # supports ID or ID#subID

        self.position = pos
        
        ## add additional arguments as fields to instance
        self.updateFields(**kwargs)

    def updateFields(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def plateid(self):
        """rack label or barcode of plate holding this sample (readonly)"""
        return self._plate.rackLabel or self._plate.barcode
    
    @property
    def plateformat(self):
        """shortcut for sample.plate.format (readonly)"""
        return self.plate.format
    
    @property
    def plate(self):
        return self._plate
    
    @plate.setter
    def plate(self, plate):
        if plate is None:
            plate = Plate()
        assert isinstance(plate, Plate)
        self._plate = plate
    
    def _setpos(self, pos):
        self._pos = self.plateformat.pos2int(pos)
    def _getpos(self):
        return self._pos
    def _getposHuman(self):
        return self.plateformat.int2human(self._pos)
    
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

        ids = [unicode(intfloat2int(x)).strip() for x in ids]
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
    
    
    def __repr__(self):
        r = '<%s %s {plate: %r, position: %i}>' % (self.__class__.__name__,
                                                   self.fullid,
                                                   self.plate,
                                                   self.position)
        return r
    
    def __str__(self):
        return self.__repr__()
    
    def __eq__(self, o):
        if not isinstance(o, self.__class__):
            return False
        if self.fullid != o.fullid:
            return False
        
        return self.plate == o.plate and self.position == o.position
    

class SampleValidationError:
    pass

class SampleConverter(object):
    """default converter for generating Sample instances from dictionaries"""

    #: class to be used and enforced for entries
    sampleClass = Sample
    
    #: rename input dict keys to standard field names {'synonym' : 'standard'}
    key2field = {K.column_subid : 'subid',
                 K.column_id : 'id',
                 K.column_plate : 'plate',
                 K.column_pos : 'pos',
                 'position': 'pos'
                 }
    
    #: fields to subject to clean2str method (convert e.g. 1.0 to unicode '1')
    fields2strclean = ['id', 'subid']
    
    def __init__(self, plateindex=E.plates):
        self.plateindex = plateindex
        
    def clean2str(self, x):
        """convert integer floats to int (if applicable), then strip to unicode"""
        x = intfloat2int(x)

        if type(x) is not unicode:
            x = unicode(x)

        x = x.strip()
        return x


    def cleanDict(self, d):
        """
        Pre-processing of dictionary values.
        """
        r = {}
        
        for key, value in d.items():
            key = key.lower()
            
            if key in self.key2field:
                key = self.key2field[key]
            
            if key in self.fields2strclean:
                value = self.clean2str(value)
            
            r[key] = value

        return r

    def isvalid(self, sample):
        """@return True, if entry is a valid Sample instance"""
        assert isinstance(sample, self.sampleClass)
        return True

    def validate(self, sample):
        """
        @return Sample, validated Sample instance
        @raise SampleValidationError, if entry is not a valid Sample instance
        """
        if not self.isvalid(sample):
            raise SampleValidationError, '%r is not a valid Sample' % sample
        return sample
    
    def getplate(self, plateid):
        """
        @param plateid: str, plate ID (typically rackLabel)
        @return Plate, matching plate instance or default plate of PlateIndex
        """
        assert type(plateid) in [str, unicode]
        r = self.plateindex.get(plateid, None)
        r = r or Plate(plateid, format=self.plateindex.defaultformat)
        return r

    def tosample(self, d):
        """
        Convert a dictionary into a new Sample instance or validate an existing
        Sample instance.
        @param d - dict OR Sample
        @return Sample, validated Sample instance
        """
        if isinstance(d, self.sampleClass):
            return self.validate(d)
    
        d = self.cleanDict(d)
        
        if not isinstance(d['plate'], Plate):
            d['plate'] = self.getplate(d['plate'])
        
        r = self.sampleClass(**d)
        
        return self.validate(r)
    
    def todict(self, sample):
        if isinstance(sample, dict):
            return sample
        
        assert isinstance(sample, self.sampleClass)
        r = {K.column_id : sample.id,
             K.column_subid : sample.subid,
             K.column_plate : sample.plateid,
             K.column_pos : sample.position}
        return r
 

from collections import MutableSequence

class SampleList(MutableSequence):
    """
    List of Sample instances. Implements full list interface.
    
    Items can be added as dictionaries, which will then be converted to
    Sample instances using the ``converterclass`` (default: SampleConverter).
    During conversion, plate IDs are converted into references to Plate
    instances which are looked up from the given PlateIndex 
    (default: the static instance evoware.plates).
    """

    def __init__(self, data=None, plateindex=E.plates,
                 converterclass=SampleConverter):
        """
        @param data: Sequence, list of dict or Sample instances
        @param plateindex: PlateIndex, from which plate instances are looked up
        @param converterclass: class, SampleConverter will be initialized with
                               the plateindex and needs to have .tosample(v)
                               method
        """
        super(SampleList, self).__init__()
        self._list = []
        self._plateindex = plateindex
        self._converter = converterclass(plateindex=plateindex)

        if data:
            for i, val in enumerate(data):
                self.insert(i,val)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, i):
        return self._list[i]

    def __delitem__(self, i):
        del self._list[i]

    def __setitem__(self, i, val):
        self._list[i] = self._converter.tosample( val )
        return self._list[i]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return """<SampleList %s>""" % self._list

    def insert(self, i, val):
        val = self._converter.tosample(val)
        self._list.insert(i, val)

    def append(self, val):
        list_idx = len(self._list)
        self.insert(list_idx, val)
    
    def toSampleIndex(self, keyfield='fullid'):
        r = {}
        for sample in self._list:
            key = eval('sample.%s' % keyfield)
            if not key in r:
                r[key] = sample
                
        return r

######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test Sample"""

    TAGS = [ testing.NORMAL ]

    def prepare(self):
        """Called once"""
        import evoware.fileutil as F
        self.f_parts = F.testRoot('partslist.xls')
        
        E.plates.clear()  ## reset PlateIndex

    def test_sample(self):
        s = Sample(id='BBa1000', subid=1.0, plate=Plate('plateA'), pos='A1')
        
        self.assertEqual(s.id, 'BBa1000')
        self.assertEqual(s.subid, '1')
        self.assertEqual(s.fullid, 'BBa1000#1')
        self.assertEqual(s.position, 1)
        self.assertEqual(s.plateid, 'plateA')
        self.assertEqual(s.position2D, 'A1')
        self.assertEqual(s.plateformat, PlateFormat(96))
        
        s.id = 'BBa2000'
        self.assertEqual(s.id, 'BBa2000')
        self.assertEqual(s.subid, '')
        self.assertEqual(s.fullid, 'BBa2000')
        
        s.id = 'BBa3000#a'
        self.assertEqual(s.id, 'BBa3000')
        self.assertEqual(s.subid, 'a')
        
        s2 = Sample(id='BBa1000#1', plate=Plate('plateA'), pos=1)
        self.assertEqual(s2.subid, '1')
        
    def test_sampleconverter(self):
        plate = E.plates.getcreate('plateA', Plate('plateA'))
        
        d1 = dict(id='BBa1000', subid=1.0, plate=plate, pos='A1')
        s1 = SampleConverter().tosample(d1)
        
        s2 = Sample(id='BBa1000#1', plate=E.plates['plateA'], pos=1)
        self.assertEqual(s1, s2)

    def test_samplelist(self):
        import evoware.excel.xlsreader as X
        r = X.XlsReader()
        r.read(self.f_parts)
        
        # generate SampleList from list of dict, generated by XlsReader
        l = SampleList(r.rows)
        self.assertEqual(len(l), 27)
        
        # validate samples with default plate format (no format given for SB10)
        self.assert_(l[3].fullid == 'sb0102#2')
        self.assert_(l[4].fullid == 'sb0103')
        self.assert_(l[3].plate.format.n == 96)
        self.assert_(l[3].position2D == 'A5')
        
        # validate records with custom plate format (format statement for SB11)
        self.assert_(l[7].fullid == 'sb0104#3')
        self.assert_(l[7].plate.format == PlateFormat(384))
        self.assertEqual(l[7].position2D, 'P1')
        
        # replace list entries from dict or Sample instance
        l[0] = Sample('testsample0', plate=Plate('testplate',format=PlateFormat(24)),
                      pos=8)
        l[1] = {'ID':'testsample1', 'sub-id':'A', 'plate':'SB11', 'pos':'I1'}
        
        self.assert_(l[0].subid == '')
        
        # manipulate plate format after initial assignment
        self.assertEqual(l[0].position2D, 'D2')
        l[0].plate.format = PlateFormat(12)
        self.assertEqual(l[0].position2D, 'B3')
        self.assert_(l[0].plateid == 'testplate')
        
        # validate new Sample is attached to plate SB11 from Excel table
        self.assert_(l[1].plate.format.n == 384)
        self.assert_(l[1].plate == l[7].plate)
        
        self.assertEqual(l[1].fullid, 'testsample1#A')
        self.assertEqual(l[1].position, 9)
        
        # test IndexGeneration
        sindex = l.toSampleIndex()
        self.assertEqual(len(sindex), len(l)-3) # 3 duplicate ID entries
        self.assertEqual(sindex['sb0102#2'], l[3])
        self.assertEqual(sindex['sb0103'], l[4])

    def test_samplelist_unknownplates(self):
        """
        ensure unknown plates are created with default format but correct ID.
        """
        reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]

        l = SampleList(reagents, plateindex=E.plates)
        
        self.assertEqual(l[0].plate.rackLabel, 'R01')
        self.assertEqual(l[1].plate.rackLabel, 'R02')
        self.assertEqual(l[0].plate.format, E.plates.defaultformat)
            