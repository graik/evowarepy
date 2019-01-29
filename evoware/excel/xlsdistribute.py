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
"""Parse Excel file for reagent distribution"""

import evoware as E

from evoware.excel import xlsreader as X
from evoware.excel import keywords as K

class DistributionXlsReader(X.XlsReader):
    """
    DistributionXlsReader is adding a 'reagents' and 'volumes' field to the 
    XlsReader class.
    (Note: the name could probably be better)
    
    Example:
    >>> reader.reagents = [{'ID': Buffer01', 'plate': 'Reservoir1', 'pos'=1}]
    >>> reader.volumes =  {'Buffer01' : 10.0}
    
    Reagents are attempted to be read from 'reagent' records and volumes from
    'volume' records at the beginning of the Excel document. These records can 
    come in any order but the 'reagent' or 'volume' keyword MUST be in the 
    first column and the lines containing them must be located before the 
    main body of the table which is typically demarkated by an "ID" keyword
    in the first colum (indicating the table header line). 
    
    The reagents list can be converted into a (source) SampleList or can be
    directly passed on to DistributionConverter.
    
    Note: 
    
        Depending on the converter used, the main body of the excel table can
        also contain volume information. `DistributionConverter` expects volume
        values in each reagent column and will therefore actually ignore the
        volumes defined in the table header.
        
        `PickingConverter`, on the other hand, can read volumes either from a 
        seperate '<field>_volume' column or from the 'volume' : field record
        in the table header.
    
    Todo:
        test case for volume record missing
    """
    
    def __init__(self, **kwarg):
        super(DistributionXlsReader,self).__init__(**kwarg)
        self.reagents = []
        self.volumes = {}
    
    def parseReagentParam(self, values, keyword=K.reagent):
        if values:
            v0 = values[0]
    
            if v0 and isinstance(v0, str) and v0.lower() == keyword:
                try:
                    key = str(values[1]).strip()
                    return {'ID':key, 'plate':values[2], 'pos':values[3]}
                except Exception as error:
                    raise ExcelFormatError('cannot parse reagent record: %r' \
                          % values)
        return {}
            
    def parseVolumeParam(self, values, keyword=K.volume):
        if values:
            v0 = values[0]
    
            if v0 and isinstance(v0, str) and v0.lower() == keyword:
                try:
                    key = str(values[1]).strip()
                    self.volumes[key] = float(values[2])
                    return True
                
                except Exception as error:
                    raise ExcelFormatError('cannot parse volume record: %r' \
                          % values)
        return False
    
    def parsePreHeader(self, values):
        super(DistributionXlsReader, self).parsePreHeader(values)
        
        if self.parseVolumeParam(values):
            return

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
