##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2019 Raik Gruenberg
from . import samples as S
from . import worklist as W

class SampleWorklist(W.Worklist):
    """
    High-level worklist operating on `Sample` and
    `Reaction` instances.
    """
    
    def transferSample(self, src, dst, volume, wash=True ):
        """
        Single volume transfer from one to another sample.
        
        Args:
            src (`Sample`): source sample instance
            dst (`Sample`): destination sample instance
            volume (int | float): volume to be transferred
            wash (bool): include wash / tip change statement after dispense
        """
        self.A(src.plate.preferredID(), src.position, volume, 
               byLabel=src.plate.byLabel(), rackType=src.plate.rackType)
        
        self.D(dst.plate.preferredID(), dst.position, volume, wash=wash, 
               byLabel=dst.plate.byLabel(), rackType=dst.plate.rackType)        
    
    def getReagentKeys(self, targetsamples):
        """
        collect all source/reagent sample IDs from all target samples
        """
        assert isinstance(targetsamples, S.SampleList)
        keys = []
        
        for ts in targetsamples:
            assert isinstance(ts, S.Reaction)
            for k in ts.sourceIds():
                if not k in keys:
                    keys.append(k)
        
        return keys
    
    def distributeSamples(self, targetsamples, reagentkeys=(), wash=True):
        """
        Variable reagent transfer to many target samples. The ``reagentkeys``
        field allows to limit the source positions / samples and can also be
        used to spefify the order in which the transfer is occuring. Otherwise
        all the source samples listed in any of the given ``targetsamples`` will
        be transferred. In order to optimize tip and plate handling, transfers
        are grouped by source reagent.
        
        Todo:
            support limited wash only after each column/reagent has been processed
        
        Args:
            targetsamples (list of `Reaction`), destination positions with 
                reference to source samples and source volumes
            reagentkeys (tuple of str): source sample IDs (column headers) to
                process; defaults to all
            wash (bool): include wash / tip change statement after dispense
        """
        keys = reagentkeys or self.getReagentKeys(targetsamples)
        
        ## operate column-wise for optimal tip/plate handling
        for k in keys:
            for tsample in targetsamples:
                assert isinstance(tsample, S.Reaction)
                
                srcsample, vol = tsample.sourceIndex().get(k, (None, None))
                
                if srcsample and vol:
                    self.transferSample(srcsample, tsample, vol, wash=wash)


######################
### Module testing ###

from . import testing

class Test(testing.AutoTest):
    """Test SampleWorklist"""

    TAGS = [ testing.NORMAL ]

    def prepare( self ):
        """reset package plate index between tests"""
        import evoware as E
        import tempfile

        E.plates.index.clear()
        self.f_worklist = tempfile.mktemp(suffix=".gwl", prefix='test_distributewl_')

    def cleanUp( self ):
        from . import fileutil as F
        if not self.DEBUG:
            F.tryRemove(self.f_worklist)


    def test_distributeworklist(self):
        from .sampleconverters import DistributionConverter
        import evoware as E
        from evoware import plates
        
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

        plates.index['T01'] = plates.Plate('T01', format=plates.PlateFormat(384))

        converter = DistributionConverter(plates.index, reagents=reagents)

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
