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
    
    Usage:
    
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
    
    Equality and Hashing:
    
    Different PlateFormat instances compare equal if they have the same
    nx and ny dimensions. This also applies to hashing. If used as dict keys,
    nx and ny determine whether two PlateFormat instances are considered the
    same key or not. For example::
    
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
        
        @param n: int, number of wells (e.g. 96)
        @param nx: int, optionally, number of columns (else calculated from n)
        @param ny: int, optionally, number of rows (else calculated from nx)
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
        @param pos: str, like 'A1' or '12'
        @return (str, int) - uppercase letter or '', number
        """
        assert type(pos) in [unicode, str]
        match = self.ex_position.match(pos)
        if not match:
            return '', None
        letter, number = match.groups()
        return letter.upper(), int(number)
    
    def pos2int(self, pos):
        """
        Convert input position to Tecan numbering
        @param pos: str | int | float, e.g. 'A2' or 'a2' or 2 or 2.0
        @return int, plate position according to Tecan numbering ('B1'=>9)

        @raise PlateError, if the resulting position is outside well number
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
            raise PlateError, 'plate position %r exceeds number of wells' % r
        if not r:
            raise PlateError, 'invalid plate position: %r' % pos
        
        return r
    
    def int2human(self, pos):
        """
        Convert Tecan well position (e.g. running from 1 to 96) into human-
        readable plate coordinate such as 'A1' or 'H12'.
        @param pos: int, well position in Tecan numbering
        @return str, plate coordinate
        """
        assert type(pos) is int
        
        col = int((pos-1) / self.ny)
        row = int((pos-1) % self.ny)
        
        if col+1 > self.nx or row > self.ny:
            raise PlateError, 'position outside plate dimensions'
        
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
    
    Fields:
    
    * rackLabel -- labware or rack label as fixed in deck layout within Evoware
    * barcode -- rack ID, usually dynamically determined by barcode reader
    * format -- plates.PlateFormat instance with number of rows and columns;
                default is 96 well format
                
    Properties:
    
    * rackType -- labware type (string) required by worklist commands if plates
                  are identified by barcode rather than rackLabel;
    
    The getter method of this property can automatically update this rack
    type string with the number of wells set in the current format. This is
    best explained with an example:

    >>> plate = Plate(barcode='0001', rackType='%i Well Microplate', 
                      format=PlateFormat(96))
    >>> plate.rackType
        "96 Well Microplate"
    
    >>> plate.format = PlateFormat(384)
    >>> plate.rackType
        "384 Well Microplate"
    
    This mechanism kicks in if there is a "%i" place holder detected anywhere
    within the given rackType string. "%i Well Microplate" is the default, so
    the above example works also if no rackType is given.
    
    Methods:
    
    byLabel() -> bool
    Can be used to set the "byLabel" flag in several worklist commands. Returns
    True if the plate has a non-empty rackLabel field. Returns False if the
    plate has a valid pair of barcode and rackType. Otherwise raises a
    PlateError.
    
    isequal(other) -> bool
    Alternative equality testing between plate instances. 

    As the fields of Plate remain mutable, __eq__ was left untouched so that
    Plate instances are hashable by instance identity.
    Instead there is a custom 'isequal' method that compares the content of 
    Plate instances.
    """
    
    def __init__(self, rackLabel='', barcode='', format=PlateFormat(96),
                 rackType='%i Well Microplate', **kwargs):
        """
        @param rackLabel - str, labware (rack) label in Evoware script
        @param barcode - str, rack ID, typically determined by barcode reader
        @param format - plates.PlateFormat, default: PlateFormat(96)
        @param rackType - str, labware (rack) type; required when using barcode
                          Note: a %i placeholder will, at run time, be replaced 
                          by current number of wells
        @kwargs - any additional keyword args will be merged as fields
        """
        assert isinstance(rackLabel, basestring)
        assert isinstance(barcode, basestring)
        assert isinstance(format, PlateFormat)
        
        self.rackLabel = rackLabel
        self.barcode = barcode
        self.format = format
        
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
        """set a new rackType; a %i placeholder will be replaced"""
        assert isinstance(value, basestring)
        self._rackType = value
    
    def isequal(self, o):
        """plate1.isequal(plate2) -> True if all their fields are equal"""
        if self is o:
            return True
        return (self.rackLabel==o.rackLabel and self.barcode==o.barcode and \
                self.format==o.format and self.rackType==o.rackType)
    
    def __repr__(self):
        return '<Plate %s : %s (%i wells)>' % (self.rackLabel,self.barcode,
                                               self.format.n )
    
    def byLabel(self):
        """
        @return True, if plate can be identified by rackLabel in worklists
        @return False, if plate can be identified by barcode and rackType
        @raise PlateError, if neither is possible
        """
        if self.rackLabel:
            return True
        if self.barcode and self.rackType:
            return False
        raise PlateError, \
              'cannot identify plate by either label or (barcode + type)'
    
    def preferredID(self):
        """
        @return rackLabel if available, otherwise return barcode
        @raise PlateError, if neither is available or rackType is missing for
                           barcode
        """
        if self.byLabel():
            return self.rackLabel
        return self.barcode


######################
### Module testing ###
import testing

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
        
        self.assert_(p1.isequal(p2))
        self.assert_(not p1.isequal(p3))
        
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