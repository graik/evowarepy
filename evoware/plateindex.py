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
    
    * getformat(key) -> will return the plates.PlateFormat instance of the plate
                      mapped to key. If the key is missing, a default format
                      is returned.
    
    Special Properties:
    
    * defaultplate -> a Plate instance for missing entries
    
    * defaultformat -> specifies the PlateFormat returned for missing keys    
                      
    A singleton (static) instance of PlateIndex is provided by evoware.__init__
    >>> import evoware as E
    >>> E.plates
    {}
    
    """
    
    #: dict key for entry with default plate (format)
    DEFAULT_KEY = 'default'
    
    def __setitem__(self, key, value):
        if not isinstance(value, Plate):
            raise TypeError('cannot assign %r to PlateIndex' % value)
        
        super(PlateIndex, self).__setitem__(key, value)    
    
    @property
    def defaultplate(self):
        if self.DEFAULT_KEY in self:
            return self[self.DEFAULT_KEY]
        return Plate(rackLabel=self.DEFAULT_KEY, format=PlateFormat(96))

    @defaultplate.setter
    def defaultplate(self, plate):
        self[self.DEFAULT_KEY] = plate

    @property
    def defaultformat(self):
        """
        Get the default PlateFormat for plates for which there is no entry
        in the index. Typically, this is the format assigned to the special
        plate 'default' (see DEFAULT_KEY). If such a 'default' record doesn't
        exist, PlateFormat(96) will be returned.
        @return PlateFormat
        """
        return self.defaultplate.format
    
    @defaultformat.setter
    def defaultformat(self, plateformat):
        """
        Assign a new default PlateFormat. If there is no 'default' plate entry
        yet, it will be created.
        @param plateformat: PlateFormat
        """
        assert isinstance(plateformat, PlateFormat)
        
        if self.DEFAULT_KEY in self:
            plate = self[self.DEFAULT_KEY]
            plate.format = plateformat
        else:
            plate = Plate(self.DEFAULT_KEY, format=plateformat)
            self[self.DEFAULT_KEY] = plate
    
    def getformat(self, key, default=None):
        """
        Get plate format assigned to plate with given ID.
        @param key: str, plate ID
        @param default: PlateFormat, if given, will be returned for missing keys
                        otherwise the defaultformat of the index is returned
        @return PlateFormat
        """
        if not key in self:
            if default:
                return default
            return self.defaultformat

        return self[key].format
    
    def getcreate(self, k, d=None):
        """
        Get existing or return new Plate instance and add it to the index. If
        no default is given, an approximate clone of the current defaultplate
        is made and assigned rackLabel=k. 
        @param k: str, plate ID / key
        @param d: Plate, default plate instance; return and add if not k in
               index
        """
        if k in self:
            return self[k]

        if d is None:
            p = self.defaultplate
            d = Plate(rackLabel=k, format=p.format, rackType=p.rackType)

        self[k] = d
        return d
    
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
                raise PlateIndexError('plate %r has no rack label' % plate)
            if key in r:
                raise PlateIndexError('duplicate rack label %s' % key)
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
                raise PlateIndexError('plate %r has no barcode' % plate)
            if key in r:
                raise PlateIndexError('duplicate barcode %s' % key)
            r[key] = plate
        return r


######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test PlateIndex"""

    TAGS = [ testing.NORMAL ]
    
    def prepare(self):
        ## plates.clear()    ## prevent spill-over from other module tests
        pass

    def test_plateindex(self):
        plates = PlateIndex()
        
        ids = ['plate%02i' % i for i in range(10)]
        formats = [PlateFormat(n) for n in [ 1,2,6,12,24,48,96,384,1536,96 ]]
        
        # create 10 plates with different IDs and formats
        l = [ Plate(rackLabel=s, barcode='bc_%s'%s, format=f) 
                  for s,f in zip(ids,formats) ]
        
        # add plates to package-wide index
        plates.update({p.rackLabel : p for p in l})
        d = plates
        
        for key, f in zip(ids,formats):
            self.assertEqual(d.getformat(key), PlateFormat(f.n))
            self.assertTrue(d[key].byLabel())
            self.assertEqual(key, d[key].rackLabel)
        
        #d['plate01'] = Plate(rackLabel='plate01', format=PlateFormat(1))
        
        d2 = d.indexByLabel()
        self.assertTrue(len(d2)==len(d))
        
        d2 = d.indexByBarcode()
        self.assertTrue(len(d2)==len(d))
        self.assertTrue(d2['bc_plate01'] == d['plate01'])
        
        self.assertEqual(d.getformat('plate01'), PlateFormat(2))
        self.assertEqual(d.getformat('unknown'), d.defaultformat)
        d.defaultformat = PlateFormat(384)
        self.assertEqual(d.getformat('unknown'), PlateFormat(384))
        
        p1 = d.getcreate('testplateA')
        p2 = d.getcreate('testplateA')
        self.assertTrue(p1 is p2)


if __name__ == '__main__':
    
    testing.localTest()