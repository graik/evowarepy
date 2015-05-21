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
    True
    >>> tsample.sourcevolumes.values() == [15.0, 100.0]
    True
    >>> tsample.sourceItems() == [(src1, 15.0), (src2, 100.0)]
    True
    >>> 
    """
        
    def updateFields(self, sourcevolumes={}, **kwargs):
        assert isinstance(sourcevolumes, dict)
        
        self.sourcevolumes = sourcevolumes
        
        super(TargetSample,self).updateFields(**kwargs)
    
    def sourceItems(self):
        """
        Pair each source sample with associated source volume.
        sample.sourceItems() == sample.sourcevolumes.items()
        @return [ (Sample, float_volume) ]
        """
        return self.sourcevolumes.items()


class PickListConverter(S.SampleConverter):
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
        
        super(PickListConverter,self).__init__(plateindex)
        
        self.sampleindex = sourcesamples.toSampleIndex()
        
        self.sourcefields = sourcefields
        self.defaultvolumes = defaultvolumes
    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, S.Sample):
                return False
        
        return super(PickListConverter, self).isvalid(sample)
    
    
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
     
        r = super(PickListConverter,self).tosample(d)
        return r
    

class DistributionListConverter(S.SampleConverter):
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
        @param sourcefields: [str], name of field(s) giving source volume
        """
        super(DistributionListConverter,self).__init__(plateindex)
    
        self.reagents = S.SampleList(reagents, plateindex=plateindex)
        self.reagents = self.reagents.toSampleIndex()
    
        self.sourcefields = sourcefields

    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, S.Sample):
                return False
        
        return super(DistributionListConverter, self).isvalid(sample)


    def tosample(self, d):
        
        sourcevolumes = {}
        
        for f in self.sourcefields:
            
            src_sample = self.reagents[f]
            src_volume = float(d.get(f, 0))
            
            sourcevolumes[src_sample] = src_volume
        
        d['sourcevolumes'] = sourcevolumes
        
        return super(DistributionListConverter, self).tosample(d)


class SampleWorklist(W.Worklist):
    """
    """

    def __init__(self, fname, targetsamples, reportErrors=True):
        """
        """
        super(SampleWorklist, self).__init__(fname, reportErrors=reportErrors)

        assert isinstance(targetsamples, S.SampleList)
        
        self.targets = targetsamples



######################
### Module testing ###
import testing

class Test(testing.AutoTest):
    """Test GoodCodeTemplate"""

    TAGS = [ testing.LONG ]

    def prepare( self ):
        """reset package plate index between tests"""
        import evoware as E
        E.plates.clear()
    
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
        
        conv = PickListConverter(sourcesamples=src_samples, 
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
    
        c = DistributionListConverter(reagents=reagents, sourcefields=fields)
        
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
        
        c2 = DistributionListConverter(reagents=reagent_instances, 
                                       sourcefields=fields)
        tsample2 = c2.tosample({'ID':'1a', 'plate':'T01', 'pos':10,
                              'reagent1': 20, 'reagent2': 100})
        
        self.assertEqual(tsample2, tsample)
        
        
    
if __name__ == '__main__':

    testing.localTest()
