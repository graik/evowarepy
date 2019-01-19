##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved
import samples as S
import worklist as W
import targetsample as TS

class SampleWorklist(W.Worklist):
    """
    High-level worklist operating on `S.Sample` and
    `TS.TargetSample` instances.
    """
    
    def transferSample(self, src, dst, volume, wash=True ):
        """
        @param src: Sample, source sample instance
        @param dst: Sample, destination sample instance
        @param volume: int | float, volume to be transferred
        @param wash: bool, include wash / tip change statement after dispense
        """
        self.A(src.plate.preferredID(), src.position, volume, 
               byLabel=src.plate.byLabel(), rackType=src.plate.rackType)
        
        self.D(dst.plate.preferredID(), dst.position, volume, wash=wash, 
               byLabel=dst.plate.byLabel(), rackType=dst.plate.rackType)        
    
    def getReagentKeys(self, targetsamples):
        """collect all source/reagent sample IDs from all target samples"""
        assert isinstance(targetsamples, S.SampleList)
        keys = []
        
        for ts in targetsamples:
            assert isinstance(ts, TS.TargetSample)
            for k in ts.sourceIds():
                if not k in keys:
                    keys.append(k)
        
        return keys
    
    def distributeSamples(self, targetsamples, reagentkeys=(), wash=True):
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
                assert isinstance(tsample, TS.TargetSample)
                
                srcsample, vol = tsample.sourceIndex().get(k, (None, None))
                
                if srcsample and vol:
                    self.transferSample(srcsample, tsample, vol, wash=wash)


######################
### Module testing ###

import testing

class Test(testing.AutoTest):
    """Test SampleWorklist"""

    TAGS = [ testing.NORMAL ]

    def prepare( self ):
        """reset package plate index between tests"""
        import evoware as E
        import tempfile

        E.plates.clear()
        self.f_worklist = tempfile.mktemp(suffix=".gwl", prefix='test_distributewl_')

    def cleanUp( self ):
        import fileutil as F
        if not self.DEBUG:
            F.tryRemove(self.f_worklist)


    def test_distributeworklist(self):
        from sampleconverters import DistributionConverter
        import evoware as E
        
        freference = ['A;R01;;;1;;20;;;\n', 'D;T01;;;10;;20;;;\n', 'W;\n', 
                      'A;R01;;;1;;40;;;\n', 'D;T01;;;11;;40;;;\n', 'W;\n', 
                      'A;R02;;;1;;100;;;\n','D;T01;;;10;;100;;;\n','W;\n']

        freference2= ['A;R01;;;1;;20;;;\n', 'D;T01;;;10;;20;;;\n', 
                      'A;R01;;;1;;40;;;\n', 'D;T01;;;11;;40;;;\n',
                      'A;R02;;;1;;100;;;\n','D;T01;;;10;;100;;;\n']

        reagents = [ {'ID':'reagent1', 'plate': 'R01', 'pos': 1},
                     {'ID':'reagent2', 'plate': 'R02', 'pos': 'A1'} ]

        samples = [ {'ID':'1#a', 'plate':'T01', 'pos':10, 
                     'reagent1': 20, 'reagent2': 100},
                    {'ID':'2#a', 'plate':'T01', 'pos':11, 
                     'reagent1': 40, 'reagent2': 0} ]

        E.plates['T01'] = E.Plate('T01', format=E.PlateFormat(384))

        converter = DistributionConverter(E.plates, reagents=reagents)

        tsamples = S.SampleList(samples, converter=converter)

        with SampleWorklist(self.f_worklist, reportErrors=True) as wl:
            wl.distributeSamples(tsamples)
        fcontent = open(self.f_worklist).readlines()
        self.assertEqual(fcontent, freference)

        with SampleWorklist(self.f_worklist, reportErrors=True) as wl:
            wl.distributeSamples(tsamples, wash=False)

        fcontent = open(self.f_worklist).readlines()
        self.assertEqual(fcontent, freference2)

if __name__ == '__main__':

    testing.localTest()
