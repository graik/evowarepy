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
"""microplate format handling"""

import numpy as N
import re, string

class PlateError(Exception):
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
    
    * by rack label -- this means the evoware script has defined a `rackLabel`
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


######################
### Module testing ###
from . import testing

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
        

if __name__ == '__main__':
    
    testing.localTest()