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
"""map source samples to target samples"""

import numbers
from . import samples as S

class TargetSample(S.Sample):
    """
    Track the reagent transfer from one or more source samples to a single
    target sample.
    
    TargetSample thus consolidates information such as 
    "take 10 ul from plate 1, well A1 and take 5 ul from plate 2, well B1 and
    combine both into target well plate 3, A1"
    
    TargetSample introduces one additional field to Sample:
    
    * sourcevolumes -- maps source Samples to volume that should be picked
    
    Various source samples and volumes can therefore be mapped to a single
    target sample.
    
    **Usage:**
    
    >>> targetplate = evoware.plates['PCR-A']  # get a Plate instance
    >>>
    >>> src1 = Sample('reagent1', plate='source1', pos='A1')
    >>> src2 = Sample('reagent2', plate='source1', pos='B1')
    >>> pick_dict = { src1: 15, src2: 100}
    >>>
    >>> tsample = TargetSample(id='Bba0000#a', plate=targetplate, pos='B2',
                               sourcevolumes=pick_dict)
    
    The `sourcevolumes` property will then look like this:
    
    >>> tsample.sourcevolumes.keys() == [src1, src2]
    >>> tsample.sourcevolumes.values() == [15.0, 100.0]
    
    
    There are several convenience methods to access the source sample
    information:
    
    >>> tsample.sourceItems() == [(src1, 15.0), (src2, 100.0)]
    >>> tsample.sourceIds() == ('reagent1', 'reagent2')
    >>>
    >>> tsample.sourceIndex() == {'reagent1' : (src1, 15.0),
                                  'reagent2' : (src2, 100.0)}
    """
    
    def __init__(self, **kwargs):
        """
        Keyword Args:
            id (str | float | int | tuple): sample ID or tuple of (id, subid)
            subid (str | float | int): sub-ID, e.g. to distinguish samples 
                   with equal content
            plate (`Plate` | str): Plate instance, or plate ID for looking up
                   plate from evoware.plates. If no plate is given, the
                   default plate instance from `evoware.plates` will be
                   assigned.
            sourcevolumes (`dict`): dict mapping source `Sample` 
                   instances to volume
        """
        self.sourcevolumes = {}
        self._sindex = None
        super(TargetSample, self).__init__(**kwargs)
        
    def updateFields(self, sourcevolumes={}, **kwargs):
        """
        Keyword Args:
            sourcevolumes (`dict`): dict mapping source `Sample` 
                   instances to volume
        """
        assert isinstance(sourcevolumes, dict)
        
        if len(sourcevolumes) > 0:
            assert isinstance(list(sourcevolumes.keys())[0], S.Sample)
            assert isinstance(list(sourcevolumes.values())[0], numbers.Number )
            
        self.sourcevolumes = sourcevolumes
        
        super(TargetSample,self).updateFields(**kwargs)
    
    def sourceItems(self):
        """
        Pair each source sample with associated source volume.
        `sample.sourceItems() == sample.sourcevolumes.items()`
        
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

######################
### Module testing ###
from . import testing

class Test(testing.AutoTest):
    """Test GoodCodeTemplate"""

    TAGS = [ testing.NORMAL ]

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

        self.assertCountEqual(sources1, sources2)

