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
        @param well: str, like 'A1' or '12'
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
            raise PlateError, 'plate position exceeds number of wells'
        
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
        

if __name__ == '__main__':
    
    testing.localTest()