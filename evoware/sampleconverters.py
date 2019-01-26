##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2019 Raik Gruenberg
"""Parse dictionaries (from Excel files) for reagent distribution"""

import collections as C
from numbers import Number

import evoware as E
import evoware.util as U
import evoware.worklist as W

from evoware.samples import Sample, SampleError, SampleList
from evoware.targetsample import TargetSample
from evoware.excel import keywords as K
from evoware.plate import Plate, PlateError

class SampleValidationError(Exception):
    pass

class SampleConverter(object):
    """default converter for generating Sample instances from dictionaries"""

    #: class to be used and enforced for entries
    sampleClass = Sample
    
    #: rename input dict keys to standard field names. 
    #: This is a dict mapping 'synonym' to 'standard field name'
    key2field = {K.column_subid : 'subid',
                 K.column_id : 'id',
                 K.column_plate : 'plate',
                 K.column_pos : 'pos',
                 'position': 'pos'
                 }
    
    #: fields to subject to clean2str method (convert e.g. 1.0 to unicode '1')
    fields2strclean = ['id', 'subid']
    
    def __init__(self, plateindex=E.plates):
        """
        Constructor.
        
        Args: 
            plateindex (`PlateIndex`): mapping plate IDs to Plate instances. 
               This defaults to the central `plates` index in the evoware 
               name space
        """
        self.plateindex = plateindex
        
    def clean2str(self, x):
        """convert integer floats to int (if applicable), then strip to string"""
        x = U.intfloat2int(x)

        if type(x) is not str:
            x = str(x)

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
        """
        Return True if entry is a valid sample.
        
        Returns:
            bool: True, if entry is a valid Sample instance
        """
        assert isinstance(sample, self.sampleClass)
        return True

    def validate(self, sample):
        """
        Returns:
            `Sample`: validated Sample instance
        Raises:
            `SampleValidationError`: if entry is not a valid Sample instance
        """
        if not self.isvalid(sample):
            raise SampleValidationError('%r is not a valid Sample' % sample)
        return sample
    
    def getcreatePlate(self, plateid):
        """
        Fetch existing or create a new plate with given plate ID.
        
        Args:
            plateid (str): plate ID, typically corresponding to rackLabel
        Returns:
            `Plate`: matching plate instance or new one created by 
                `PlateIndex`
        """
        assert isinstance(plateid, str)
        return self.plateindex.getcreate(plateid)

    def tosample(self, d):
        """
        Convert a dictionary into a new Sample instance or validate an existing
        Sample instance.
        
        Args:
            d (dict | `Sample`): dict with sample fields or `Sample` instance
        Returns:
            `Sample`: validated Sample instance
        """
        if isinstance(d, self.sampleClass):
            return self.validate(d)
    
        d = self.cleanDict(d)
        
        if not isinstance(d['plate'], Plate):
            d['plate'] = self.getcreatePlate(d['plate'])
        
        r = self.sampleClass(**d)
        
        return self.validate(r)
    
    def todict(self, sample):
        """
        Convert a sample instance into a dictionary (or return an existing
        dictionary unmodified).
        
        Args:
            sample (`Sample` | dict): input Sample instance or sample dict
        Returns:
            dict: a dictionary
        """
        if isinstance(sample, dict):
            return sample
        
        assert isinstance(sample, self.sampleClass)
        r = {K.column_id : sample.id,
             K.column_subid : sample.subid,
             K.column_plate : sample.plateid,
             K.column_pos : sample.position}
        return r
 

class PickingConverter(SampleConverter):
    """
    Convert dictionaries or Sample instances to TargetSample instances.

    This converter assumes a "pick list" input where each "row" contains:
       - one or more source columns (sourcefields) pointing to a source 
         sample ID
    
       - optional "<source>_volume" columns where <source> corresponds to
         a source field
        
    If not given in a separate row, volumes can be specified column-wide
    using the defaultvolumes dictionary {<str source> : <int volume>}.
    
    If a given record contains no '<source>_volume' entry, the volume is looked
    up from defaultvolumes['<source>']. If there is no default volume defined
    for this source field, a volume of 0 is assigned.
    """
    
    sampleClass = TargetSample
    
    def __init__(self, plateindex=E.plates, sourcesamples=[], 
                 sourcefields=['source'], defaultvolumes={} ):
        """
        Constructor.
        
        Args: 
            plateindex (`PlateIndex`): mapping plate IDs to Plate instances
            sourcesamples (`SampleList`): to match source sample IDs to Samples
            sourcefields ([str]): name of field(s) pointing to source sample
            defaultvolumes (dict): map each or some source field(s) to 
                a default volume. E.g. Should look like {'buffer' : 10}.
        """
        
        super(PickingConverter,self).__init__(plateindex)
        
        self.sampleindex = sourcesamples.toSampleIndex()
        
        self.sourcefields = sourcefields
        self.defaultvolumes = defaultvolumes
    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, Sample):
                return False
        
        return super(PickingConverter, self).isvalid(sample)
    
    
    def volumefield(self, field):
        return '%s_volume' % field
    
    def tosample(self, d):
        sourcevolumes = {}
        
        for f in self.sourcefields:
            
            src_sample = d[f]
            if not isinstance(src_sample, Sample):
                src_sample = self.sampleindex[ src_sample ]
            
            volume_field = self.volumefield(f)
            sample_vol = d.get(volume_field, self.defaultvolumes.get(f,0))
            
            sourcevolumes[ src_sample ] = float(sample_vol)
        
        d['sourcevolumes'] = sourcevolumes
     
        r = super(PickingConverter,self).tosample(d)
        return r
    

class DistributionConverter(SampleConverter):
    """
    Convert dictionaries or Sample instances to TargetSample instances.
    
    This converter assumes a "volume distribution" input format where volumes
    to distribute are variable and listed in columns with the reagent name
    used as a column header.
    
    Example:
    
    >>> reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]
    >>>
    >>> fields = ['reagent1', 'reagent2']
    >>>
    >>> c = DistributionListConverter(reagents=reagents, sourcefields=fields)
    >>>
    >>> tsample = c.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
    """
   
    sampleClass = TargetSample
    
    def __init__(self, plateindex=E.plates, reagents=[], sourcefields=[] ):
        """
        Constructor.
        
        Args:
            plateindex (`PlateIndex`): index of all known plates 
                (default is evoware.plates)
            reagents (`SampleList` or list of dict): sample IDs *must* match 
                source fields
            sourcefields (list of str): names of reagent/volume field(s) 
                to process, default: all reagent IDs
        """
        super(DistributionConverter,self).__init__(plateindex)
    
        self.reagents = SampleList(reagents)
        self.reagents = self.reagents.toSampleIndex()
    
        self.sourcefields = sourcefields or list(self.reagents.keys())

    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, Sample):
                return False
        
        return super(DistributionConverter, self).isvalid(sample)


    def tosample(self, d):
        
        sourcevolumes = {}
        
        for f in self.sourcefields:
            
            src_sample = self.reagents[f]
            src_volume = float(d.get(f, 0) or 0)  ## '' == '0' == '0.0' == 0
            
            sourcevolumes[src_sample] = src_volume
        
        d['sourcevolumes'] = sourcevolumes
        
        return super(DistributionConverter, self).tosample(d)



from . import testing

class Test(testing.AutoTest):
    """Test sampleconverters"""

    TAGS = [ testing.LONG ]

    def prepare( self ):
        """reset package plate index between tests"""
        import evoware as E
        E.plates.clear()
            
    def test_sampleconverter(self):
        plate = E.plates.getcreate('plateA', Plate('plateA'))
        
        d1 = dict(id='BBa1000', subid=1.0, plate=plate, pos='A1')
        s1 = SampleConverter().tosample(d1)
        
        s2 = Sample(id='BBa1000#1', plate=E.plates['plateA'], pos=1)
        self.assertEqual(s1, s2)

    
    def test_pickingconverter(self):
        import evoware as E
        
        E.plates['target'] = E.Plate('target')
        
        sourceplate = E.Plate('SRC')
    
        src_sample1 = Sample('R01', plate=sourceplate, pos=1)
        src_sample2 = Sample('R02#b', plate=sourceplate, pos=2)
        
        src_samples = SampleList([src_sample1, src_sample2])
        
        conv = PickingConverter(sourcesamples=src_samples, 
                                     sourcefields=['reagent1', 'reagent2'], 
                                     defaultvolumes={'reagent1':15} )
        
        rawsample = {'ID': 'reaction1', 'plate': 'target', 'position':'A2',
                     'reagent1': 'R01', 'reagent2': 'R02#b', 
                     'reagent2_volume': 100}
        
        tsample = conv.tosample(rawsample)
        
        sources2 = tsample.sourceItems()
        sources1 = [ (src_sample1, 15.0), (src_sample2, 100.0) ]
    
        self.assertCountEqual(sources1, sources2)
        
        
    def test_distributionConverter(self):
        import evoware as E

        reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]

        fields = ['reagent1', 'reagent2']
    
        c = DistributionConverter(reagents=reagents, sourcefields=fields)
        
        self.assertEqual(len(E.plates), 2)  # should have inserted the two reagent plates by now

        tsample = c.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
        
        reagent_instances = SampleList(reagents)
        
        self.assertCountEqual(list(tsample.sourcevolumes.values()), [20.0, 100.0])
        
        s1 = tsample.sourceIndex()['reagent1'][0]
        s2 = reagent_instances[0]
        self.assertTrue(s1.plate == s2.plate)
        
        self.assertCountEqual(list(tsample.sourcevolumes.keys()), reagent_instances)
        
        self.assertTrue(SampleList(reagent_instances) == SampleList(reagents))
        
        c2 = DistributionConverter(reagents=reagent_instances, 
                                       sourcefields=fields)
        tsample2 = c2.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
        
        self.assertEqual(tsample2, tsample)
        
    
if __name__ == '__main__':

    testing.localTest()
