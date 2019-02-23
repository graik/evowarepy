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
"""microplate handling"""

import numpy as N
import re, string

class PlateError(Exception):
    pass

class PlateIndexError(PlateError):
    pass


class PlateFormat(object):
    """
    Describe plate columns : rows dimensions and convert back and for between 
    'human' (e.g. 'B2') and 'Tecan' (e.g. 10) well numbering.
    
    **Usage:**
    
    >>> f = PlateFormat(96)
    >>> f.nx
    12
    >>> f.ny
    8
    >>> f.pos2int('A2')
    9
    >>> f.pos2int('h12')
    96
    >>> f.int2human(96)
    'H12'
    
    *Equality and Hashing:*
    
    Different PlateFormat instances compare equal if they have the same
    nx and ny dimensions. This also applies to hashing. If used as dict keys,
    nx and ny determine whether two PlateFormat instances are considered the
    same key or not. For example:
    
    >>> f1 = PlateFormat(12,8)
    >>> f2 = PlateFormat(96)
    >>> f1 == f2
     True
    >>> f1 is f2
     False
    >>> d = {f1: 'format_1'}
    >>> d[f2] = 'format 2'
    >>> d[f1]
     'format 2'
    """
    
    ex_position = re.compile('([A-Za-z]{0,1})([0-9]+)')
    
    
    def __init__(self, n, nx=None, ny=None):
        """
        Define Plate format. Number of columns (nx) and rows (ny) is deduced
        from well number (n), assuming a 3 : 2 ratio of columns : rows. This
        gives the expected dimensions for plates with 1, 2, 6, 12, 24, 48,
        96, 384 and 1536 wells. For any format more odd than this, nx and ny
        should be given explicitely.
        
        Args:
            n (int): number of wells (e.g. 96)
            
        Keyword Args:
            nx (int): optional, number of columns (else calculated from n)
            ny (int): optional, number of rows (else calculated from nx)
        """
        self.n = int(n)
        self.nx = int(nx or round(N.sqrt(3./2 * self.n)) )
        self.ny = int(ny or round(1.0*n/self.nx) )
        
        if self.nx * self.ny != self.n:
            raise PlateError('invalid plate format: %r x %r != %r' % \
                             (self.nx, self.ny, self.n))
    
    
    def str2tuple(self, pos):
        """
        Normalize position string to tuple.
        
        Args:
            pos (str): like 'A1' or '12'
        Returns:
            tuple: (str, int) with uppercase letter or '' and number
        """
        assert type(pos) is str
        match = self.ex_position.match(pos)
        if not match:
            return '', None
        letter, number = match.groups()
        return letter.upper(), int(number)
    
    def pos2int(self, pos):
        """
        Convert and normalize given position to standard Tecan numbering
        
        Args:
            pos (str | int | float): e.g. 'A2' or 'a2' or 2 or 2.0
        Returns:
            int: plate position according to Tecan numbering ('B1'=>9)

        Raises:
            PlateError: if the resulting position is outside well number
        """
        if type(pos) in [int, float]:
            letter, number = '', int(pos)
        else:
            letter, number = self.str2tuple(pos)
            
        if letter:
            row = string.ascii_uppercase.find(letter) + 1
            col = number
            r = (col - 1) * self.ny + row
        else:
            r = number
        
        if r > self.n:
            raise PlateError('plate position %r exceeds number of wells' % r)
        if not r:
            raise PlateError('invalid plate position: %r' % pos)
        
        return r
    
    def int2human(self, pos):
        """
        Convert Tecan well position (e.g. running from 1 to 96) into human-
        readable plate coordinate such as 'A1' or 'H12'.
        
        Args:
            pos (int): well position in Tecan numbering
        Returns:
            str: plate coordinate
        """
        assert type(pos) is int
        
        col = int((pos-1) / self.ny)
        row = int((pos-1) % self.ny)
        
        if col+1 > self.nx or row > self.ny:
            raise PlateError('position outside plate dimensions')
        
        r = string.ascii_uppercase[row] + str(col+1)
        return r
    
    def __str__(self):
        return '%i well PlateFormat' % self.n
    
    def __repr__(self):
        return '<%s>' % str(self)
    
    def __eq__(self, o):
        return isinstance(o, PlateFormat) and \
               self.n == o.n and self.nx == o.nx and self.ny == o.ny

    def __hash__(self):
        return hash((self.n, self.nx))
    

class Plate(object):
    """
    Description of an individual plate or labware object. 
    
    See Also: `PlateIndex`
    
    The main objectives of this class are:
    
        (1) to easily convert back and forth between integer labware positions
        (e.g. 1 to 96) and coordinates (e.g. 'A1' to 'H12' or 'a1' to 'h12' or
        "a01" etc.) while considering the plate format.
    
        (2) to identify a plate or labware regardless whether it is described
        by deck position or by barcode.
    
    The conversion between coordinates and "Tecan numbering" depdends on the
    following field:
    
    * format -- `PlateFormat` instance with number of rows and columns; \
                default is 96 well format
 
    **Plate identification** depends on two fields and one property:
        
    * rackLabel -- labware or rack label as fixed in deck layout within Evoware
    * barcode -- rack ID, usually dynamically determined by barcode reader   
    * rackType -- labware type (str) required by worklist commands if plates\
        are identified by barcode rather than rackLabel;

    Why are there three fields for something as simple as an ID? The problem is
    that Evoware has two mutually exclusive methods for identifying a plate:
    
    * by rack label -- this means the evoware script has defined a ``rackLabel``
      field directly on the worktable layout. This is the more common and easier
      way of finding a plate. In this case, it is the end user's responsability
      to put the correct plate on the correct position of the worktable.
          
    * by barcode -- this means the evoware script, at some point, reads in the
      barcode of a plate and then keeps track of where to find it. However, the
      barcode alone is not enough. Any worklist commands using this plate also
      need to know the `rackType` which is expected to be one of many fixed
      Labware type strings such as (by default) "96 Well Microplate".
    
    The `byLabel()` method informs whether or not a plate is identified by 
    rackLabel (True) or by barcode (False). The `preferredID()` method
    tries to completely hide this whole barcode vs. label complexity and will
    return a simple ID which can be either rackLabel or barcode, whatever seems
    appropriate.
    
    Moreover, if barcodes are used, the getter method of the `rackType`
    property can automatically update the rack type string with the number of
    wells set in the current format. This is best explained with an example:

    >>> plate = Plate(barcode='0001', rackType='%i Well Microplate', 
                      format=PlateFormat(96))
    >>> plate.rackType
        "96 Well Microplate"
    >>>
    >>> plate.format = PlateFormat(384)
    >>> plate.rackType
        "384 Well Microplate"
    
    This mechanism kicks in if there is a "%i" place holder detected anywhere
    within the given rackType string. "%i Well Microplate" is the default, so
    the above example works also if no rackType is given.
    
    A note about plate comparison: 
    As the fields of Plate remain mutable, __eq__ was left untouched so that
    Plate instances are hashable by instance identity.
    Instead there is a custom `isequal()` method that compares the content of 
    Plate instances.
    """
    
    def __init__(self, rackLabel='', barcode='', format=PlateFormat(96),
                 rackType='%i Well Microplate', **kwargs):
        """
        Create new Plate instance.
        
        Args:
            rackLabel (str): labware (rack) label in Evoware script
            barcode (str)  : rack ID, typically determined by barcode reader
            format (`PlateFormat`): default is PlateFormat(96)
            rackType (str): labware (rack) type; required when using barcode
                          Note: a %i placeholder will, at run time, be replaced 
                          by current number of wells

        Any additional keyword args will be merged in as custom fields.
        """
        assert isinstance(rackLabel, str)
        assert isinstance(barcode, str)
        assert isinstance(format, PlateFormat)
        
        self.rackLabel = rackLabel
        self.barcode = barcode  #: rack ID, usually dynamically determined by barcode reader
        self.format = format    #: `PlateFormat` instance
        
        self._rackType = rackType
        
        self.__dict__.update(**kwargs)
    
    @property
    def rackType(self):
        """optionally insert current well number into racktype string"""
        if '%i' in self._rackType:
            return self._rackType % self.format.n
        return self._rackType
    
    @rackType.setter
    def rackType(self, value):
        """
        set a new rackType; a %i placeholder will be replaced by well number
        of current `plateFormat`.
        """
        assert isinstance(value, str)
        self._rackType = value
    
    def isequal(self, o):
        """
        Alternative equality testing between plate instances. As the fields of
        Plate remain mutable, __eq__ was left untouched so that Plate instances
        are hashable by instance identity. Instead this is a custom method that
        compares the content of Plate instances.

        Returns:
            bool: True if all their standard fields are equal (custom fields
            added through the constructor are ignored).
        """
        if self is o:
            return True
        return (self.rackLabel==o.rackLabel and self.barcode==o.barcode and \
                self.format==o.format and self.rackType==o.rackType)
    
    def __repr__(self):
        return '<Plate %s : %s (%i wells)>' % (self.rackLabel,self.barcode,
                                               self.format.n )
    
    def byLabel(self):
        """
        Can be used to set the "byLabel" flag in several worklist
        commands. It returns True if the plate has a non-empty rackLabel field.
        It returns False if the plate has a valid pair of barcode and rackType.
        Otherwise it raises a PlateError.
        
        Returns:
            bool: 
                - True, if plate can be identified by rackLabel in worklists
                - False, if plate can be identified by barcode and rackType
        Raises:
            PlateError: if neither is possible
        """
        if self.rackLabel:
            return True
        if self.barcode and self.rackType:
            return False
        raise PlateError('cannot identify plate by either label or (barcode + type)')
    
    def preferredID(self):
        """
        Get whatever plate ID that is most likely to make Evoware happy. This
        means return the fixed "rackLabel" if available but otherwise return
        the dynamically determined barcode.
        
        Returns:
            str: rackLabel if available, otherwise barcode
        Raises:
            PlateError: if neither is available or if rackType is missing for
                the given barcode
        """
        if self.byLabel():
            return self.rackLabel
        return self.barcode


class PlateIndex(dict):
    """
    Dictionary of `Plate` instances. Currently, no assumption is made about
    what the keys look like -- they should be either rackLabel or barcode of
    the plates. A new index by one or the other can be created using:
    
    >>> index = plateindex.indexByLabel()
    
    and:
    
    >>> index = plateindex.indexByBarcode()
    
    Special methods:
    
    * getformat(key) -> will return the `PlateFormat` instance of the
      plate mapped to key. If the key is missing, a default format is returned.
    
    Special Properties:
    
    * defaultplate -> a `Plate` instance for missing entries
    
    * defaultformat -> specifies the `PlateFormat` returned for missing keys    
                      
    A singleton (static) instance of `PlateIndex` is provided by the module:
    
    >>> import evoware.plastes as P
    >>> P.index
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
        Get the default `PlateFormat` for plates for which there is no entry
        in the index. Typically, this is the format assigned to the special
        plate 'default' (see DEFAULT_KEY). If such a 'default' record doesn't
        exist, PlateFormat(96) will be returned.
        
        Returns: `PlateFormat`
        """
        return self.defaultplate.format
    
    @defaultformat.setter
    def defaultformat(self, plateformat):
        """
        Assign a new default PlateFormat. If there is no 'default' plate entry
        yet, it will be created.
        
        Args:
            plateformat: `PlateFormat`
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
        
        Args:
            key (str): plate ID
            default (`PlateFormat`): if given, will be returned for missing keys
               otherwise the defaultformat of the index is returned
        Returns:
            `PlateFormat`
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
        
        Args: 
            k (str): plate ID / key 
            d (`Plate`) default plate instance; return and add if `k` cannot be 
              found in index
        Returns:
            `Plate`: new or previously existing plate instance with given ID
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
        Create and return a new PlateIndex instance indexed by labware label.
        
        Returns: 
            `PlateIndex`: a new PlateIndex instance with all plates indexed 
               by rackLabel
        Raises:
            `PlateIndexError`: if any of the plates lacks a rackLabel
            `PlateIndexError`: if any two plates have the same rackLabel
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
        Create and return a new PlateIndex instance indexed by barcode.
        
        Returns:
            `PlateIndex`: a new PlateIndex instance with all plates indexed by 
               barcode
        Raises: 
            `PlateIndexError`: if any of the plates lacks a barcode
            `PlateIndexError`: if any two plates have the same barcode
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

# static `PlateIndex` instance tracking all currently known plates
index = PlateIndex() 


######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test PlateFormat"""

    TAGS = [ testing.NORMAL ]

    def test_plateformat_init(self):
        formats = {}
        for n in [6, 12, 24, 96, 384, 1536]:
            f = PlateFormat(n)
            formats[n] = f
            self.assertEqual(f.n, f.nx * f.ny, 'plate format error')
        
        self.assertEqual(formats[6].nx, 3, msg='6-well definition error')
        self.assertEqual(formats[12].nx, 4, msg='12-well definition error')
        self.assertEqual(formats[24].nx, 6, msg='24-well definition error')
        self.assertEqual(formats[96].nx, 12, msg='96-well definition error')
        self.assertEqual(formats[384].nx, 24, msg='384-well definition error')
        self.assertEqual(formats[1536].nx, 48, msg='1536-well definition error')
    
    def test_plateformat_pos2int(self):
        f = PlateFormat(96)
        self.assertEqual(f.pos2int('A1'), 1)
        self.assertEqual(f.pos2int('H1'), 8)
        self.assertEqual(f.pos2int('b1'), 2)
        self.assertEqual(f.pos2int('A2'), 9)
        self.assertEqual(f.pos2int('A12'), 89)
        self.assertEqual(f.pos2int('h12'), 96)
    
    def test_plateformat_human2int(self):
        f = PlateFormat(96)
        
        tests = ['A1', 'B1', 'H1', 'A2', 'B2', 'H2', 'A12', 'B12', 'H12']
        
        for t in tests:
            pos = f.pos2int(t)
            human = f.int2human(pos)
            self.assertEqual(t, human)
    
    def test_plateformat_eq(self):
        f1 = PlateFormat(96)
        f2 = PlateFormat(96)
        f3 = PlateFormat(96, nx=1, ny=96)
        
        self.assertTrue(f1 == f2)
        self.assertFalse(f2 == f3)
        self.assertEqual(f1,f2)
    
    def test_plate(self):
        p1 = Plate(rackLabel='srcA')
        p2 = Plate(rackLabel='srcA')
        p3 = Plate(barcode='0001', param2='extra param', 
                   format=PlateFormat(384), rackType='%i Deepwell Plate')
        
        self.assertTrue(p1.isequal(p2))
        self.assertTrue(not p1.isequal(p3))
        
        self.assertTrue(p1.byLabel())
        self.assertFalse(p3.byLabel())
        
        self.assertEqual(p3.param2, 'extra param')
        
        self.assertEqual(p3.rackType, '384 Deepwell Plate')
        self.assertEqual(p1.rackType, '96 Well Microplate')
    
##    def test_plate_nohashing(self):
##        """ensure Plates cannot be hashed"""
##        
##        def inner_call():
##            p1 = Plate('testplate')
##            d = {p1 : 'testvalue'}
##            
##        self.assertRaises(TypeError, inner_call)
        
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