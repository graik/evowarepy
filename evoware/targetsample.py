##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved

import numbers
import samples as S

class TargetSample(S.Sample):
    """
    TargetSample introduces one additional field to Sample:
    
    * sourcevolumes -- maps source Samples to volume that should be picked
    
    Various source samples and volumes can therefore be mapped to a single
    target sample.
    
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
            assert isinstance(sourcevolumes.values()[0], numbers.Number )
            
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
        return [s.fullid for s in self.sourcevolumes.keys()]

    def sourceIndex(self):
        """
        @return { str : (Sample, int_volume) }, a dict of Sample/volume tuples
                indexed by reagent ID
        """
        if not self._sindex:
            self._sindex = { ts.fullid : (ts, v) for ts,v in self.sourceItems() }
        return self._sindex    

######################
### Module testing ###
import testing

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

        self.assertItemsEqual(sources1, sources2)

