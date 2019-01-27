#!/usr/bin/env python
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
"""Reset a (worklist) file to empty; or create an empty file."""

import sys, os

import evoware.fileutil as F
import evoware.dialogs as D

def _use():
    print("""
resetfile.py -- reset file to empty (0 Byte length)

Syntax:
    resetfile.py <file>
                
If <file> exists, it will be overridden by an empty file. If <file> does not
exist, it will be created.
""")
    sys.exit(0)

###########################
# MAIN
###########################
if __name__ == '__main__':
    
    f = ''
    
    try:
        if len(sys.argv) < 2:
            _use()
            
        f = F.absfile(sys.argv[1])
        
        h = open(f, 'w')
        h.close()
        
    except Exception as why:
        D.lastException('Error resetting file %r' % f)
