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
from plateindex import plates

class TargetSample(S.Sample):
    """
    TargetSample introduces one additional field to Sample:
    
    * sourcevolumes -- maps source Samples to volume that should be picked
    
    Usage:
    
    >>> targetplate = evoware.plates['PCR-A']  # get a Plate instance
    
    >>> pick_dict = { <Sample 'reagent1' ...> : 15,
                      <Sample 'water' ...> : 100}
    
    >>> tsample = TargetSample(id='Bba0000#a', plate=targetplate, pos='B2',
                               sourcevolumes=pick_dict)
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


class TargetSampleConverter(S.SampleConverter):
    """
    Convert dictionaries or Sample instances to TargetSample instances.
    """
    
    sampleClass = TargetSample
    
    def __init__(self, plateindex=plates, sourcesamples=[], 
                 sourcefields=['source'], defaultvolumes={} ):
        
        super(TargetSampleConverter,self).__init__(plateindex)
        
        self.sampleindex = sourcesamples.toSampleIndex()
        
        self.sourcefields = sourcefields
        self.defaultvolumes = defaultvolumes
    
    def isvalid(self, sample):
        
        for srcsample, vol in sample.sourcevolumes.items():
            if not isinstance(srcsample, S.Sample):
                return False
        
        return super(TargetSampleConverter, self).isvalid(sample)
    
    
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
     
        r = super(TargetSampleConverter,self).tosample(d)
        return r

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
        pass
    
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
        
        conv = TargetSampleConverter(sourcesamples=src_samples, 
                                     sourcefields=['reagent1', 'reagent2'], 
                                     defaultvolumes={'reagent1':15} )
        
        rawsample = {'ID': 'reaction1', 'plate': 'target', 'position':'A2',
                     'reagent1': 'R01', 'reagent2': 'R02#b', 
                     'reagent2_volume': 100}
        
        tsample = conv.tosample(rawsample)
        
        sources2 = tsample.sourceItems()
        sources1 = [ (src_sample1, 15.0), (src_sample2, 100.0) ]
    
        self.assertItemsEqual(sources1, sources2)
        
        
        
        
        
    
if __name__ == '__main__':

    testing.localTest()
