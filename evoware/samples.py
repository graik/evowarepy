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
from collections.abc import MutableSequence
import numbers

import evoware as E
import evoware.util as U
from evoware.plates import PlateFormat, PlateError, Plate

class SampleError(Exception):
    pass

def normalize_sample_id(ids):
        """
        Normalizes input ID or (ID, sub-ID) tuple to standard ('ID', 'sub-ID')
        tuple.
        
        Acceptable inputs are 'ID', or ('ID', 'sub-ID') or 'ID#subID'. int or 
        float IDs or sub-IDs are also acceptable but will be cleaned up and
        converted to str. "cleaned up" here means that float input 1.0 will be
        converted first to int 1 and then str '1'.
        
        Args: 
            ids (float | int | str or list thereof): input ID[,subID]
        
        Returns:
            tuple: (str_ID, str_subID) or (str_ID, '') 
        """
        if type(ids) is str and '#' in ids:
            ids = ids.split('#')

        if type(ids) not in [tuple, list]:
            ids = (ids,)

        ids = [str(U.intfloat2int(x)).strip() for x in ids]
        ids = [ x for x in ids if x ]  ## filter out empty strings but not '0'
        
        _id = ids[0] if len(ids) > 0 else ''
        _subid = ids[1] if len(ids) > 1 else ''
        
        return _id, _subid


class Sample(object):
    """
    Representation of a single well / sample.
    
    Sample is considered immutable. All sub-fields have to be specified via
    the constructor and are then available as read-only properties.
    
    For convenience, Sample can be imported directly from the evoware package
    name space:: 

        from evoware import Sample

    *Properties:*
    
        * `id` - str, main sample ID 
        * `subid` - str, secondary ID to, e.g., distinguish replicas and clones
        * `fullid` - str, gives id#subid if there is a subid, else just id.
        
        * `plate` - a `Plate` instance
        * `plateformat` - shortcut to the plate's PlateFormat (row:column dimensions)
        * `plateid` - shortcut to plate.rackLabel *or* plate.barcode
        
        * `position` - int, well position, e.g. number 1 to 96
        * `position2D` - str, human readable well position (e.g. 'A1')

    *Usage:*
    
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
            
        ... which results in an additional 'temperature' field:
        
            >>> s.temperature
                25
        
    *Equality and hashing:*
    
        ID + subID + plate + position determine the identity of a sample:
        
        >>> s1 = Sample('s1', 'a', 'plateA', 1)
        >>> s2 = Sample('s1#a', plate=evoware.plates.index['plateA'], pos='A1')
        >>> s1 == s2
        True
        >>> s1 is s2
        False

        >>> d = {s1 : 'some value'}
        >>> d[s2] == 'some value'
        True
    """
    
    def __init__(self, id='', subid='', plate=None, pos=0,
                 **kwargs):
        """
        Keyword Args:
            id (str | float | int | tuple): sample ID or tuple of (id, subid)
            subid (str | float | int): sub-ID, e.g. to distinguish samples 
                   with equal content
            plate (`Plate` | str): Plate instance, or plate ID for looking up
                   plate from evoware.plates.index. If no plate is given, the
                   default plate instance from ``evoware.plates.index`` will be
                   assigned.
        """        
        self._subid = str(U.intfloat2int(subid)).strip()
        
        self._id = ''
        if self._subid:
            self._setid((id, subid))
        else:
            self._setid(id)   # supports ID or ID#subID

        if isinstance(plate, str):
            plate = E.plates.index.getcreate(plate)
        
        self._plate = plate or E.plates.index.defaultplate
        assert isinstance(self._plate, Plate)
        
        self._pos = self.plateformat.pos2int(pos)
        
        self._hashcache = None
        self._fullidcache = None
                
        ## add additional arguments as fields to instance
        self.updateFields(**kwargs)

    def updateFields(self, **kwargs):
        """add additional fields to sample instance (used by constructor)"""
        self.__dict__.update(kwargs)

    @property
    def id(self):
        """main sample ID (without sub-ID); or empty str"""
        return self._id

    @property
    def subid(self):
        """sub-ID if any; otherwise empty str"""
        return self._subid

    def _getfullid(self):
        if self._subid:
            return '#'.join((self._id, self._subid))
        return self._id

    @property
    def fullid(self):
        """complete ID which can be either ID or ID#subID"""
        if self._fullidcache is None:
            self._fullidcache = self._getfullid()
        return self._fullidcache

    @property
    def plate(self):
        """-> Plate, readonly property"""
        return self._plate
        
    @property
    def position(self):
        """
        -> int (readonly), well position of this sample within plate. On a 96
        well plate, numbers run row-wise from upper left (1 = A1) to lower
        right (96 = H12). Position 8 would be H1, 9 would be B1 etc.
        """
        return self._pos

    @property
    def plateid(self):
        """rack label or barcode of plate holding this sample (readonly)"""
        return self._plate.rackLabel or self._plate.barcode

    @property
    def plateformat(self):
        """shortcut for sample.plate.format (readonly)"""
        return self.plate.format

    @property
    def position2D(self):
        """
        str (read-only), 'human readable' version of the well position. E.g.
        'A1', 'B2', 'H12', etc.
        """
        return self.plateformat.int2human(self._pos)

    def _setid(self, ids):
        """
        Assign new ID and (optionally) sub-id.
        
        Normalizes input ID or (ID, sub-ID) tuple or ID#subID string into pair
        of main ID and optional sub-ID. See `normalize_sample_id`.
        
        Args:
            ids (float | int | str | unicode or list): input ID or ID+subID
        """
        self._id, self._subid = normalize_sample_id(ids)
    
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
    
    def __hash__(self):
        if self._hashcache:
            return self._hashcache
        self._hashcache = hash((self.fullid, self._plate, self._pos))
        return self._hashcache

    
class Reaction(Sample):
    """
    Track the reagent transfer from one or more source samples to a single
    target sample.
    
    Reaction thus consolidates information such as 
    "take 10 ul from plate 1, well A1 and take 5 ul from plate 2, well B1 and
    combine both into target well plate 3, A1"
    
    Reaction introduces one additional field to Sample:
    
    * sourcevolumes -- maps source Samples to volume that should be picked
    
    Various source samples and volumes can therefore be mapped to a single
    target sample.
    
    **Usage:**
    
    >>> targetplate = evoware.plates.index['PCR-A']  # get a Plate instance
    >>>
    >>> src1 = Sample('reagent1', plate='source1', pos='A1')
    >>> src2 = Sample('reagent2', plate='source1', pos='B1')
    >>> pick_dict = { src1: 15, src2: 100}
    >>>
    >>> reaction = Reaction(id='Bba0000#a', plate=targetplate, pos='B2',
                               sourcevolumes=pick_dict)
    
    The ``sourcevolumes`` property will then look like this:
    
    >>> reaction.sourcevolumes.keys() == [src1, src2]
    >>> reaction.sourcevolumes.values() == [15.0, 100.0]
    
    
    There are several convenience methods to access the source sample
    information:
    
    >>> reaction.sourceItems() == [(src1, 15.0), (src2, 100.0)]
    >>> reaction.sourceIds() == ('reagent1', 'reagent2')
    >>>
    >>> reaction.sourceIndex() == {'reagent1' : (src1, 15.0),
                                  'reagent2' : (src2, 100.0)}
    """
    
    def __init__(self, **kwargs):
        """
        Keyword Args:
            id (str | float | int | tuple): sample ID or tuple of (id, subid)
            subid (str | float | int): sub-ID, e.g. to distinguish samples 
                   with equal content
            plate (`Plate` | str): Plate instance, or plate ID for looking up
                   plate from evoware.plates.index. If no plate is given, the
                   default plate instance from evoware.`plates.index` will be
                   assigned.
            sourcevolumes (dict): dict mapping source `Sample` 
                   instances to volume
        """
        self.sourcevolumes = {}
        self._sindex = None
        super().__init__(**kwargs)
        
    def updateFields(self, sourcevolumes={}, **kwargs):
        """
        Keyword Args:
            sourcevolumes (dict): dict mapping source `Sample` 
                   instances to volume
        """
        assert isinstance(sourcevolumes, dict)
        
        if len(sourcevolumes) > 0:
            assert isinstance(list(sourcevolumes.keys())[0], Sample)
            assert isinstance(list(sourcevolumes.values())[0], numbers.Number )
            
        self.sourcevolumes = sourcevolumes
        
        super().updateFields(**kwargs)
    
    def sourceItems(self):
        """
        Pair each source sample with associated source volume.
        ``sample.sourceItems() == sample.sourcevolumes.items()``
        
        Returns:
           list of dict: [ (`Sample`, float_volume) ]
        """
        return self.sourcevolumes.items()
    
    def sourceIds(self):
        """
        Returns:
            list of str: the fullID of each source sample, aka the reagent key
            or column header in a reagent distribution
        """
        return [s.fullid for s in self.sourcevolumes.keys()]

    def sourceIndex(self):
        """
        Returns:
            dict: { str : (`Sample`, int_volume) } 
            a dict of (`Sample`,volume) tuples indexed by reagent ID
        """
        if not self._sindex:
            self._sindex = { ts.fullid : (ts, v) for ts,v in self.sourceItems() }
        return self._sindex    


class SampleList(MutableSequence):
    """
    List of Sample instances. Implements full list interface.
    
    Items can be added as dictionaries, which will then be converted to
    Sample instances using the ``converter`` (default: `SampleConverter`).
    During conversion, plate IDs are converted into references to Plate
    instances which are looked up from the given `PlateIndex` 
    (default: the static instance evoware.plates.index).
    """

    def __init__(self, data=None, converter=None):
        """
        Keyword Args:
            data (Sequence): list of dict or Sample instances
            converter (`SampleConverter`): SampleConverter instance
                needs to have .tosample(v) method [default: `SampleConverter`]
        """
        from evoware.sampleconverters import SampleConverter
        
        super().__init__()
        
        converter = converter or SampleConverter()
        assert isinstance(converter, SampleConverter)
        
        self._list = []
        self._converter = converter

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
    
    def insert(self, i, val):
        assert isinstance(val, Sample) or isinstance(val, dict)
        val = self._converter.tosample(val)
        self._list.insert(i, val)

    def __eq__(self, o):
        return self._list == o

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return """<SampleList %s>""" % self._list

    def toSampleIndex(self, keyfield='fullid'):
        """
        Create an "index dictionary" with sample instances indexed by their
        ID. Duplicate entries (with identical ID#subID) will be skipped.
        
        Keyword Args:
            keyfield (str): the sample field or property to use as an index key
                (default: 'fullid')
        Returns:
            dict: {'ID' : `Sample`}
        """
        r = {}
        for sample in self._list:
            key = eval('sample.%s' % keyfield)
            if not key in r:
                r[key] = sample
                
        return r


class SampleIndex:
    """
    Index mapping `Sample` instances to their full ID (ID#subID). The class
    behaves similar to a dict but does not implement the full dictionary 
    interface.
    """
    
    def __init__(self, initialdata=None, relaxed_id=True):
        """
        Keyword Args:
            initialdata (SampleList): initial Sample instances
            relaxed_id (bool): fall back to matching by only main ID if sub-ID 
                is not given, for example:
                parts['Bba001'] may return parts['Bba001#a']
        """
        self.relaxed = relaxed_id
        self._map = {}
        if initialdata:
            self.extend(initialdata)

    def add(self, sample:Sample):
        """
        Add a new `Sample` instance to the index.
        
        Note:
            If another sample was already registered with the same ID#subID
            combination, it will be silently overridden. This may lead to 
            some unexpected side effects if redundant sample lists are read.
            
        Args:
            sample (`Sample`): sample instance to be added
        """
        if not isinstance(sample, Sample):
            raise ValueError('%r not allowed in SampleDict' % type(sample))
        
        self._map[ sample.fullid ] = sample
    
    def extend(self, samples):
        """
        Add several samples to index.
        
        Args:
           samples (Sequence): list of `Sample` instances (or `SampleList`)
        """
        for v in samples:
            self.add(v)
    
    def get(self, key, default=None, relaxed=None) -> Sample:
        """
        Supports three different calling patterns:
            index[ 'ID' ] -> (first) sample with main ID=='ID'
            index[ 'ID#subID' ] -> sample with ID=='ID' and subID=='subID'
            index[ 'ID', 'subID' ] -> same as above
        
        Args:
            key (str): Sample ID or ID#subID or tuple of (ID, subID)
            
        Keyword Args:
            default (`Sample`): default value to return if key is not found
            relaxed (bool): override *relaxed_id* setting from constructor

        Returns:
            `Sample`: `Sample` matching ID or ID#subID

        Raise:
            KeyError: if given ID doesn't match any sample
        """
        
        key, _subid = normalize_sample_id(key)   
        if _subid:
            key = '#'.join((key, _subid))
        
        if relaxed is None:
            relaxed = self.relaxed

        if relaxed and not key in self._map:
            for k in self._map.keys():
                if k.split('#')[0] == key:
                    return self._map[k]
        
        try:
            return self._map[key]
        except KeyError:
            if default is not None:
                return default
            raise
    
    def __getitem__(self, key) -> Sample:
        return self.get(key)
    
    def __len__(self):
        return len(self._map)
    
    def keys(self):
        return self._map.keys()
    
    def values(self):
        return self._map.values()
    
    def items(self):
        return self._map.items()

    def __delitem__(self, key):
        """
        Remove given sample.
        
            >>> del index[key]
        
        Args:
            key (str or `Sample`): either sample ID or a `Sample` instance
        """
        if type(key) is str:
            sample = self[key]
            del self._map[sample.fullid]
        
        if isinstance(key, Sample):
            del self._map[key.fullid]

        raise ValueError('%r not allowed' % type(key))


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
        self.f_primers = F.testRoot('primers.xls')
        
        E.plates.index.clear()

    def test_sample(self):
        s = Sample(id='BBa1000', subid=1.0, plate=Plate('plateA'), pos='A1')
        
        self.assertEqual(s.id, 'BBa1000')
        self.assertEqual(s.subid, '1')
        self.assertEqual(s.fullid, 'BBa1000#1')
        self.assertEqual(s.position, 1)
        self.assertEqual(s.plateid, 'plateA')
        self.assertEqual(s.position2D, 'A1')
        self.assertEqual(s.plateformat, PlateFormat(96))
        
        s = Sample(id='BBa2000', pos=1)
        self.assertEqual(s.id, 'BBa2000')
        self.assertEqual(s.subid, '')
        self.assertEqual(s.fullid, 'BBa2000')
        
        s = Sample(id='BBa3000#a', pos=1)
        self.assertEqual(s.id, 'BBa3000')
        self.assertEqual(s.subid, 'a')
        
        s2 = Sample(id='BBa1000#1', plate=Plate('plateA'), pos=1)
        self.assertEqual(s2.subid, '1')
    
    def test_sample_hashing(self):
        s1 = Sample('s1', 'a', 'plateA', 1)
        s2 = Sample('s1#a', plate=E.plates.index['plateA'], pos='A1')

        self.assertTrue(s1 == s2)
        self.assertTrue(s1 is not s2)
        
        d = {s1 : 'some value'}
        self.assertTrue(d[s2] == 'some value')
    
    def test_reaction(self):
        sourceplate = Plate('SRC')
        targetplate = Plate('testplate')

        src_sample1 = Sample('R01', plate=sourceplate, pos=1)
        src_sample2 = Sample('R02#b', plate=sourceplate, pos=2)

        src_volumes = {src_sample1: 15, src_sample2: 100}

        tsample = Reaction(id='Bba0000#a', plate=targetplate, pos='B2',
                               sourcevolumes=src_volumes)

        sources2 = tsample.sourceItems()
        sources1 = [ (src_sample1, 15.0), (src_sample2, 100.0) ]

        self.assertCountEqual(sources1, sources2)


    def test_samplelist(self):
        import evoware.excel.xlsreader as X
        import evoware.samples as S
        r = X.XlsReader()
        r.read(self.f_parts)
        
        # generate SampleList from list of dict, generated by XlsReader
        l = SampleList(r.rows)
        self.assertEqual(len(l), 27)
        
        # validate samples with default plate format (no format given for SB10)
        self.assertTrue(l[3].fullid == 'sb0102#2')
        self.assertTrue(l[4].fullid == 'sb0103')
        self.assertTrue(l[3].plate.format.n == 96)
        self.assertTrue(l[3].position2D == 'A5')
        
        # validate records with custom plate format (format statement for SB11)
        self.assertTrue(l[7].fullid == 'sb0104#3')
        self.assertTrue(l[7].plate.format == PlateFormat(384))
        self.assertEqual(l[7].position2D, 'P1')
        
        # replace list entries from dict or Sample instance
        l[0] = S.Sample('testsample0', plate=Plate('testplate',format=PlateFormat(24)),
                      pos=8)
        l[1] = {'ID':'testsample1', 'sub-id':'A', 'plate':'SB11', 'pos':'I1'}
        
        self.assertTrue(l[0].subid == '')
        
        # manipulate plate format after initial assignment
        self.assertEqual(l[0].position2D, 'D2')
        l[0].plate.format = PlateFormat(12)
        self.assertEqual(l[0].position2D, 'B3')
        self.assertTrue(l[0].plateid == 'testplate')
        
        # validate new Sample is attached to plate SB11 from Excel table
        self.assertTrue(l[1].plate.format.n == 384)
        self.assertTrue(l[1].plate == l[7].plate)
        
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
        import evoware.samples as S ## enforce evoware.samples namespace
        
        reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]

        l = S.SampleList(reagents)
        
        self.assertEqual(l[0].plate.rackLabel, 'R01')
        self.assertEqual(l[1].plate.rackLabel, 'R02')
        self.assertEqual(l[0].plate.format, E.plates.index.defaultformat)
        
        ## test re-creating a sample list
        l2 = S.SampleList(l)
        self.assertEqual(l, l2)
    
    def test_sampleindex(self):
        import evoware.excel.xlsreader as X
        import evoware.samples as S  ## enforce evoware.samples namespace
        
        xls = X.XlsReader()
        xls.read(self.f_parts)
        srcsamples = S.SampleList(xls.rows)
        
        xls = X.XlsReader()
        xls.read(self.f_primers)
        primers = S.SampleList(xls.rows)
        
        index = S.SampleIndex(srcsamples, relaxed_id=True)
        index.extend(primers)
        
        self.assertIs(index['sb0101'], index['sb0101#2'])
        self.assertIs(index['sb0104'], index['sb0104#1'])
        self.assertIs(index['sb0106'], index['sb0106','a'])
        
        self.assertEqual(index['sb0103'].fullid, 'sb0103')
        self.assertEqual(index['sb0104','4'].fullid,'sb0104#4')
        self.assertEqual(index['sbo0002'].position, 2)
        
        ## partslist.xls contains 3 duplicate entries with identical ID#subID
        self.assertEqual(len(index), len(primers) + len(srcsamples) -3)


if __name__ == '__main__':

    testing.localTest()
