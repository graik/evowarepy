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
"""Protoype script for generating PCR setup worklist from Excel files"""

import sys
import evoware.util as U
import evoware.fileutil as F
import evoware.cherrypicking as P

def _use( options ):
    print """
pcrsetup.py -- Generate PCR setup worklist from part index and cherry picking
               Excel files.

Syntax:
    pcrsetup.py -i <reactions.xls> -src <templates.xls> <primers.xls>
                [-useRack ]

Options:
    -i        input excel file listing which source samples should be pipetted
              into which target wells
    -src      one or more Excel files listing the position(s) of source samples
              in source plates
    -useRack  interpret plate IDs in tables as Evo RackLabel (Labware label)
              otherwise, plate IDs are interpreted as $Labware.ID$

Default options:
"""
    for key, value in options.items():
        print "\t-",key, "\t",value

    sys.exit(0)

def _defaultOptions():
    return {}

def cleanOptions( options ):
    options['i'] = F.absfile(options['i'])
    options['src'] = [ F.absfile(f) for f in U.tolist(options['src']) ]
    options['useRack'] = 'useRack' in options
    return options

###########################
# MAIN
###########################

if len(sys.argv) < 5:
    _use( _defaultOptions() )
    
options = U.cmdDict( _defaultOptions() )

try:
    options = cleanOptions(options) 
except KeyError:
    _use(options)


