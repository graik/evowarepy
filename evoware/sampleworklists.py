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

"""Generate worklists for cherry picking and reagent distribution"""
import collections as C
from numbers import Number

import worklist as W
import samples as S
import evoware as E

class TargetSample(S.Sample):
    """
    TargetSample introduces one additional field to Sample:
    
    * sourcevolumes -- maps source Samples to volume that should be picked
    
    Usage:
    
    >>> targetplate = evoware.plates['PCR-A']  # get a Plate instance
    
    >>> src1 = Sample('reagent1', plate='source1', pos='A1')
    >>> src2 = Sample('reagent2', plate='source1', pos='B1')
    
    >>> pick_dict = { src1 : 15,
                      src2 : 100}
    
    >>> tsample = TargetSample(id='Bba0000#a', plate=targetplate, pos='B2',
                               sourcevolumes=pick_dict)
    
    >>> tsample.sourcevolumes.keys() == [src1, src2]
    
    >>> tsample.sourcevolumes.values() == [15.0, 100.0]
    
    
    There are several convenience methods to access the source sample
    information:
    
    >>> tsample.sourceItems() == [(src1, 15.0), (src2, 100.0)]
    
    >>> tsample.sourceIds() == ('reagent1', 'reagent2')
    
    >>> tsample.sourceIndex() == {'reagent1' : (src1, 15.0),
                                  'reagent2' : (src2, 100.0)}
    """
    def __init__(self, **kwargs):
        self.sourcevolumes = {}
        self._sindex = None
        super(TargetSample, self).__init__(**kwargs)
        
    def updateFields(self, sourcevolumes={}, **kwargs):
        """
        @param sourcevolumes: {Sample : int_volume}
        """
        assert isinstance(sourcevolumes, dict)
        
        if len(sourcevolumes) > 0:
            assert isinstance(sourcevolumes.keys()[0], S.Sample)
            assert isinstance(sourcevolumes.values()[0], Number )
            
        self.sourcevolumes = sourcevolumes
        
        super(TargetSample,self).updateFields(**kwargs)
    
    def sourceItems(self):
        """
        Pair each source sample with associated source volume.
        sample.sourceItems() == sample.sourcevolumes.items()
        @return [ (Sample, float_volume) ]
        """
        return self.sourcevolumes.items()
    
    def sourceIds(self):
        """
        @return (str,), the fullID of each source sample, aka the reagent key
                        or column header in a reagent distribution
        """
        return (s.fullid for s in self.sourcevolumes.keys())

    def sourceIndex(self):
        """
        @return { str : (Sample, int_volume) }, a dict of Sample/volume tuples
                indexed by reagent ID
        """
        if not self._sindex:
            self._sindex = { ts.fullid : (ts, v) for ts,v in self.sourceItems() }
        return self._sindex    

class PickingConverter(S.SampleConverter):
    """
    Convert dictionaries or Sample instances to TargetSample instances.

    This converter assumes a "pick list" input where each row contains:
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
        @param plateindex: PlateIndex, mapping plate IDs to Plate instances
        @param sourcesamples: SampleList, to match source sample IDs to Samples
        @param sourcefields: [str], name of field(s) pointing to source sample
        @param defaultvolumes: {str:int}, map each or some source field(s) to 
                               a default volume
        """
        
        super(PickingConverter,self).__init__(plateindex)
        
        self.sampleindex = sourcesamples.toSampleIndex()
        
        self.sourcefields = sourcefields
        self.defaultvolumes = defaultvolumes
    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, S.Sample):
                return False
        
        return super(PickingConverter, self).isvalid(sample)
    
    
    def volumefield(self, field):
        return '%s_volume' % field
    
    def tosample(self, d):
        sourcevolumes = {}
        
        for f in self.sourcefields:
            
            src_sample = d[f]
            if not isinstance(src_sample, S.Sample):
                src_sample = self.sampleindex[ src_sample ]
            
            volume_field = self.volumefield(f)
            sample_vol = d.get(volume_field, self.defaultvolumes.get(f,0))
            
            sourcevolumes[ src_sample ] = float(sample_vol)
        
        d['sourcevolumes'] = sourcevolumes
     
        r = super(PickingConverter,self).tosample(d)
        return r
    

class DistributionConverter(S.SampleConverter):
    """
    Convert dictionaries or Sample instances to TargetSample instances.
    
    This converter assumes a "volume distribution" input format where volumes
    to distribute are variable and listed in columns with the reagent name
    used as a column header.
    
    Example:
    
    >>> reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]

    >>> fields = ['reagent1', 'reagent2']
    
    >>> c = DistributionListConverter(reagents=reagents, sourcefields=fields)
    
    >>> tsample = c.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
    """
   
    sampleClass = TargetSample
    
    def __init__(self, plateindex=E.plates, reagents=[], 
                 sourcefields=['source'] ):
        """
        @param plateindex: PlateIndex, mapping plate IDs to Plate instances
        @param reagents: SampleList or [{}], sample IDs *must* match source fields
        @param sourcefields: [str], names of reagent/volume field(s) 
                             to process, default: all reagent IDs
        """
        super(DistributionConverter,self).__init__(plateindex)
    
        self.reagents = S.SampleList(reagents, plateindex=plateindex)
        self.reagents = self.reagents.toSampleIndex()
    
        self.sourcefields = sourcefields or self.reagents.keys()

    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, S.Sample):
                return False
        
        return super(DistributionConverter, self).isvalid(sample)


    def tosample(self, d):
        
        sourcevolumes = {}
        
        for f in self.sourcefields:
            
            src_sample = self.reagents[f]
            src_volume = float(d.get(f, 0))
            
            sourcevolumes[src_sample] = src_volume
        
        d['sourcevolumes'] = sourcevolumes
        
        return super(DistributionConverter, self).tosample(d)


import excel as X
import excel.keywords as K

class DistributionXlsReader(X.XlsReader):
    
    def __init__(self, **kwarg):
        super(DistributionXlsReader,self).__init__(**kwarg)
        self.reagents = {}
    
    def parseReagentParam(self, values, keyword=K.reagent):
        if values:
            v0 = values[0]
    
            if v0 and isinstance(v0, basestring) and v0.lower() == keyword:
                try:
                    key = unicode(values[1]).strip()
                    return {'ID':key, 'plate':values[2], 'pos':values[3]}
                except Exception, error:
                    raise ExcelFormatError, 'cannot parse reagent record: %r' \
                          % values
        return {}
            
    def parsePreHeader(self, values):
        super(DistributionXlsReader, self).parsePreHeader(values)
        self.reagents.update( self.parseReagentParam(values) )


class SampleWorklist(W.Worklist):
    """
    """
    
    def transferSample(self, src, dst, volume, wash=True ):
        """
        @param src: Sample, source sample instance
        @param dst: Sample, destination sample instance
        @param volume: int | float, volume to be transferred
        @param wash: bool, include wash / tip change statement after dispense
        """
        self.A(src.preferredID(), src.position, volume, byLabel=src.byLabel(), 
               rackType=src.plate.rackType)
        
        self.D(dst.preferredID(), dst.position, volume, wash=wash, 
               byLabel=dst.byLabel(), rackType=dst.rackType)        
    
    def getReagentKeys(self, targetsamples):
        """collect all source/reagent sample IDs from all target samples"""
        assert isinstance(targetsamples, S.SampleList)
        keys = set()
        
        for ts in targetsamples:
            assert isinstance(ts, TargetSample)
            keys.add(ts.sourceIds())
        
        return keys
    
    def distributeSamples(self, targetsamples, reagentkeys=()):
        """
        @param targetsamples: [ TargetSample ], destination positions with 
                              reference to source samples and source volumes
        @param reagentkeys: (str,), source sample IDs (column headers) to
                            process; default: all
        """
        keys = reagentkeys or self.getReagentKeys(targetsamples)
        
        ## operate column-wise for optimal tip/plate handling
        for k in keys:
            for tsample in targetsamples:
                assert isinstance(tsample, TargetSample)
                
                srcsample, vol = tsample.sourceIndex().get(k, (None, None))
                
                if srcsample and vol:
                    self.transferSample(srcsample, tsample, vol)


######################
### Module testing ###
import testing

class Test(testing.AutoTest):
    """Test GoodCodeTemplate"""

    TAGS = [ testing.LONG ]

    def prepare( self ):
        """reset package plate index between tests"""
        import evoware as E
        import tempfile
        E.plates.clear()
        
        self.fname = tempfile.mktemp(suffix=".gwl", prefix='test_distributewl_')
    
    def cleanUp( self ):
        import fileutil as F
        if not self.DEBUG:
            F.tryRemove(self.fname)
    
    def test_targetsample(self):
        from evoware import Plate

        sourceplate = Plate('SRC')
        targetplate = Plate('testplate')
        
        src_sample1 = S.Sample('R01', plate=sourceplate, pos=1)
        src_sample2 = S.Sample('R02#b', plate=sourceplate, pos=2)
       
        src_volumes = {src_sample1: 15, src_sample2: 100}
       
        tsample = TargetSample(id='Bba0000#a', plate=targetplate, pos='B2',
                               sourcevolumes=src_volumes)
                
        sources2 = tsample.sourceItems()
        sources1 = [ (src_sample1, 15.0), (src_sample2, 100.0) ]
        
        self.assertItemsEqual(sources1, sources2)
        
    def test_targetsampleconverter(self):
        import evoware as E
        
        E.plates['target'] = E.Plate('target')
        
        sourceplate = E.Plate('SRC')
    
        src_sample1 = S.Sample('R01', plate=sourceplate, pos=1)
        src_sample2 = S.Sample('R02#b', plate=sourceplate, pos=2)
        
        src_samples = S.SampleList([src_sample1, src_sample2])
        
        conv = PickingConverter(sourcesamples=src_samples, 
                                     sourcefields=['reagent1', 'reagent2'], 
                                     defaultvolumes={'reagent1':15} )
        
        rawsample = {'ID': 'reaction1', 'plate': 'target', 'position':'A2',
                     'reagent1': 'R01', 'reagent2': 'R02#b', 
                     'reagent2_volume': 100}
        
        tsample = conv.tosample(rawsample)
        
        sources2 = tsample.sourceItems()
        sources1 = [ (src_sample1, 15.0), (src_sample2, 100.0) ]
    
        self.assertItemsEqual(sources1, sources2)
        
        
    def test_distributionConverter(self):
        import evoware as E

        reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]

        fields = ['reagent1', 'reagent2']
    
        c = DistributionConverter(reagents=reagents, sourcefields=fields)
        
        self.assertEqual(len(E.plates), 2)  # should have inserted the two reagent plates by now

        tsample = c.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
        
        reagent_instances = S.SampleList(reagents, plateindex=E.plates)
        
        self.assertItemsEqual(tsample.sourcevolumes.values(), [20.0, 100.0])
        
        s1 = tsample.sourcevolumes.keys()[0]
        s2 = reagent_instances[0]
        self.assert_(s1.plate == s2.plate)
        
        self.assertItemsEqual(tsample.sourcevolumes.keys(), reagent_instances)
        
        self.assert_(S.SampleList(reagent_instances) == S.SampleList(reagents))
        
        c2 = DistributionConverter(reagents=reagent_instances, 
                                       sourcefields=fields)
        tsample2 = c2.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
        
        self.assertEqual(tsample2, tsample)
        
    
    def test_distributeworklist(self):
        reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]
        
        samples = [ {'ID':'1#a', 'plate':'T01', 'pos':10, 
                     'reagent1': 20, 'reagent2': 100},
                    {'ID':'2#a', 'plate':'T01', 'pos':11, 
                     'reagent1': 40, 'reagent2': 0} ]
        
        E.plates['T01'] = E.Plate('T01', format=E.PlateFormat(384))
        
        converter = DistributionConverter(E.plates, reagents=reagents)
        
        tsamples = S.SampleList(samples, converter=converter)
        
        with SampleWorklist(self.fname, reportErrors=True) as wl:
            wl.distributeSamples(tsamples)
        
        pass
       
    
if __name__ == '__main__':

    testing.localTest()
