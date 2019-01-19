##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved
"""Parse Excel file for reagent distribution"""
##import collections as C
##from numbers import Number
##
##import evoware.worklist as W
##import evoware.samples as S
##from evoware.targetsample import TargetSample
import evoware as E

import xlsreader as X
import keywords as K

class DistributionXlsReader(X.XlsReader):
    """
    DistributionXlsReader is adding a 'reagents' field to the XlsReader class.
    (Note: the name could probably be better)
    
    Example:
    >>> reader.reagents = [{'ID': Buffer01', 'plate': 'Reservoir1', 'pos'=1}]
    
    Reagents are attempted to be read from @reagent records at the beginning
    of the Excel document.
    
    The reagents list can be converted into a (source) SampleList or can be
    directly passed on to DistributionConverter.
    """
    
    def __init__(self, **kwarg):
        super(DistributionXlsReader,self).__init__(**kwarg)
        self.reagents = []
    
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
        rdict = self.parseReagentParam(values)
        if rdict:
            self.reagents.append( rdict )


import evoware.testing as testing

class Test(testing.AutoTest):
    """Test GoodCodeTemplate"""

    TAGS = [ testing.LONG ]

    def prepare( self ):
        """reset package plate index between tests"""
        import evoware.fileutil as F
        import tempfile
        import evoware as E
        E.plates.clear()
        
        self.f_worklist = tempfile.mktemp(suffix=".gwl", prefix='test_distributewl_')
        self.f_xls = F.testRoot('distribution.xls')
    
    def cleanUp( self ):
        import evoware.fileutil as F
        if not self.DEBUG:
            F.tryRemove(self.f_worklist)
    
    
    def test_distributionxlsreader(self):
        from evoware.sampleconverters import DistributionConverter
        import evoware.samples as S
        
        xls = DistributionXlsReader()
        xls.read(self.f_xls)
        
        converter = DistributionConverter(reagents=xls.reagents,
                                          sourcefields=[])
        targets = S.SampleList(xls.rows, converter=converter )
        
        self.assertEqual(len(targets), 10)
        
        s, v = targets[1].sourceIndex()['buffer01']
        self.assertEqual(s.position, 1)
        self.assertEqual(v,2)
        self.assertEqual(s.plate.preferredID(), 'reservoirA')
        
        s, v = targets[6].sourceIndex()['buffer01']
        self.assertEqual(v, 0)
        s, v = targets[6].sourceIndex()['master']
        self.assertEqual(v, 0)
        self.assertEqual(s.plate.preferredID(), 'reservoirB')
        
    
if __name__ == '__main__':

    testing.localTest()
