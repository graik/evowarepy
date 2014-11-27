#!/usr/bin/env python
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
import evoware.dialogs as D
import evoware.cherrypicking as P

def _use( options ):
    print """
pcrsetup.py -- Generate PCR setup worklist from part index and cherry picking
               Excel files.

Syntax (non-interactive):
    pcrsetup.py -i <reactions.xls> -src <templates.xls> <primers.xls>
                -o <output.worklist> [-useLabel]
                
Syntax (interactive):
    pcrsetup.py -dialogs [-p <project directory>
                -o <output.worklist> -i <reactions.xls> -src <templates.xls>] 
                -useLabel]


Options:
    -dialogs  generate file open dialogs for any missing input files
              This option also activates user dialog-based error reporting.
    -p        default project directory for input and output files
    
    -i        input excel file listing which source samples should be pipetted
              into which target wells
    -src      one or more Excel files listing the position(s) of source samples
              in source plates
    -o        output file name for generated worklist
              
    -useLabel interpret plate IDs in tables as Labware label
              otherwise, plate IDs are interpreted as $Labware.ID$ (barcode)
##    -srcplate only generate worklist for transfers that can be realized with
              with given source plate(s) (identified by their ID)

If -dialogs is given, a missing -i or -o or -scr option triggers a file open
dialog(s) for the appropriate file(s).

Currently defined options:
"""
    for key, value in options.items():
        print "\t-",key, "\t",value

    sys.exit(0)

def _defaultOptions():
    return {}

def cleanOptions( options ):
    options['dialogs'] = 'dialogs' in options
    options['p'] = F.absfile( options.get('p', ''))
    
    if options['dialogs']:
        
        if not 'i' in options:
            options['i'] = D.askForFile(defaultextension='*.xls', 
                            filetypes=(('Excel classic','*.xls'),('Excel','*.xlsx'),('All files','*.*')), 
                            initialdir=options['p'], 
                            multiple=False, 
                            title="Definition of Target Reactions")
        
        if not 'src' in options:
            options['src'] = D.askForFile(defaultextension='*.xls', 
                            filetypes=(('Excel classic','*.xls'),('Excel','*.xlsx'),('All files','*.*')), 
                            initialdir=options['p'], 
                            multiple=True, 
                            title="Source templates and primers and their locations")
        
        if not 'o' in options:
            options['o'] = D.askForFile(defaultextension='*.gwl', 
                            filetypes=(('Evo Worklist','*.gwl'),('Text file','*.txt'),('All files','*.*')), 
                            initialdir=options['p'], 
                            multiple=False,
                            newfile=True,
                            title="Save Worklist output file as")
    
    
    options['i'] = F.absfile(options['i'])
    options['src'] = [ F.absfile(f) for f in U.tolist(options['src']) ]
    options['o'] = F.absfile(options['o'])
    
    options['useLabel'] = 'useLabel' in options
##    options['srcplate'] = [s.strip() for s in U.tolist(options.get('srcplate',[]))]
    return options

###########################
# MAIN
###########################

try:
    if len(sys.argv) < 2:
        _use( _defaultOptions() )
        
    options = U.cmdDict( _defaultOptions() )
    
    try:
        options = cleanOptions(options) 
    except KeyError, why:
        print 'missing option: ', why
        _use(options)
    
    parts = P.PartIndex()
    for f in options['src']:
        parts.readExcel(f)
    
    targets = P.TargetIndex(srccolumns=['template', 'primer1', 'primer2'])
    targets.readExcel(options['i'])
    
    cwl = P.CherryWorklist(options['o'], targets, parts, reportErrors=True)
    cwl.toWorklist(byLabel=options['useLabel'])
    cwl.close()

except Exception, why:
    if 'dialogs' in options:
        D.lastException('Error generating Worklist')
    else:    
        raise
