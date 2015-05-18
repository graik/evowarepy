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
"""Provides static instance 'plates' which maps IDs to plate instances"""

from evoware import PlateFormat, PlateError, Plate

class PlateIndexError(PlateError):
    pass

class PlateIndex(dict):
    """
    Dictionary of plate instances. Currently, no assumption is made about
    what the keys look like -- they should be either rackLabel or barcode of
    the plates. A new index by one or the other can be created using:
    
    >>> index = plateindex.indexByLabel()
    and
    >>> index = plateindex.indexByBarcode()
    
    Special methods:
    
    getformat(key) -> will return the plates.PlateFormat instance of the plate
                      mapped to key.
                      
    A singleton (static) instance of PlateIndex is provided by this module:
    >>> plates
    
    """
    
    def __setitem__(self, key, value):
        if not isinstance(value, Plate):
            raise TypeError, 'cannot assign %r to PlateIndex' % value
        
        super(PlateIndex, self).__setitem__(key, value)    
    
    def getformat(self, key, default=PlateFormat(96)):
        if not key in self:
            if 'default' in self:
                return self['default'].format
            return default
        return self[key].format
    
    def indexByLabel(self):
        """
        @return a new PlateIndex instance with all plates indexed by rackLabel
        @raise PlateIndexError, if any of the plates lacks a rackLabel
        @raise PlateIndexError, if any two plates have the same rackLabel
        """
        r = PlateIndex()
        for plate in self.values():
            key = plate.rackLabel
            if not key:
                raise PlateIndexError, 'plate %r has no rack label' % plate
            if key in r:
                raise PlateIndexError, 'duplicate rack label %s' % key
            r[key] = plate
        return r
    
    def indexByBarcode(self):
        """
        @return a new PlateIndex instance with all plates indexed by barcode
        @raise PlateIndexError, if any of the plates lacks a barcode
        @raise PlateIndexError, if any two plates have the same barcode
        """
        r = PlateIndex()
        for plate in self.values():
            key = plate.barcode
            if not key:
                raise PlateIndexError, 'plate %r has no barcode' % plate
            if key in r:
                raise PlateIndexError, 'duplicate barcode %s' % key
            r[key] = plate
        return r

## static instance to be used as a singleton index throughout the package
plates = PlateIndex()


######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test PlateIndex"""

    TAGS = [ testing.NORMAL ]

    def test_plateindex(self):
        ids = ['plate%02i' % i for i in range(10)]
        formats = [PlateFormat(n) for n in [ 1,2,6,12,24,48,96,384,1536,96 ]]
        
        l = [Plate(rackLabel=s, barcode='bc_%s'%s, format=f) 
                  for s,f in zip(ids,formats)]
        
        plates.update({p.rackLabel : p for p in l})
        d = plates
        
        for key, f in zip(ids,formats):
            self.assertEqual(d.getformat(key), PlateFormat(f.n))
            self.assertTrue(d[key].byLabel())
            self.assertEqual(key, d[key].rackLabel)
        
        d['plate01'] == Plate(rackLabel='plate01', format=PlateFormat(1))
        
        d2 = d.indexByLabel()
        self.assert_(len(d2)==len(d))
        
        d2 = d.indexByBarcode()
        self.assert_(len(d2)==len(d))
        self.assert_(d2['bc_plate01'] == d['plate01'])
        
