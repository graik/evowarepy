#!/usr/bin/env python
##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved"""Reset a (worklist) file to empty; or create an empty file."""

import sys, os

import evoware.fileutil as F
import evoware.dialogs as D

def _use( options ):
    print """
resetfile.py -- reset file to empty (0 Byte length)

Syntax:
    resetfile.py <file>
                
If <file> exists, it will be overridden by an empty file. If <file> does not
exist, it will be created.
"""
    sys.exit(0)

###########################
# MAIN
###########################
f = ''

try:
    if len(sys.argv) < 2:
        _use()
        
    f = F.absfile(sys.argv[1])
    
    h = open(f, 'w')
    h.close()
    
except Exception, why:
    D.lastException('Error resetting file %r' % f)
