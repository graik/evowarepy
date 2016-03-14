#!/usr/bin/env python
##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved
"""Protoype script for generating PCR setup worklist from Excel files"""

import sys, logging

import evoware.util as U
import evoware.fileutil as F
import evoware.dialogs as D

import evoware.sampleworklist as W
import evoware.samples as S
import evoware.excel as X
import evoware.sampleconverters as C

def _use( options ):
    print """
distribute.py -- Generate (variable) reagent distribution worklist from Excel file.

Syntax (non-interactive):
    distribute.py -i <distribute.xls> -o <output.worklist> 
                  [-barcode -src <sourcesamples.xls> -columns <name1 name2>]
                
Syntax (interactive):
    pcrsetup.py -dialogs [-p <project directory>
                -o <output.worklist> -i <distribute.xls> -src <sources.xls>
                -barcode]


Options:
    -dialogs  generate file open dialogs for any missing input files
              This option also activates user dialog-based error reporting.
    -p        default project directory for input and output files
    
    -i        input excel file listing target samples and which reagent volumes 
              to dispense where
    -src      (optional) specify reagent samples in separate excel file
    -o        output file name for generated worklist
              
    -barcode  interpret plate IDs in all tables as barcode ()$Labware.ID$) 
              rather than labware label
    -columns  explicitely specify which source columns to process (default: all)

If -dialogs is given, a missing -i or -o option triggers a file open
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
                            title="Distribution Table")
        
        if not 'o' in options:
            options['o'] = D.askForFile(defaultextension='*.gwl', 
                            filetypes=(('Evo Worklist','*.gwl'),('Text file','*.txt'),('All files','*.*')), 
                            initialdir=options['p'], 
                            multiple=False,
                            newfile=True,
                            title="Save Worklist output file as")
    
    
    options['i'] = F.absfile(options['i'])
    if 'src' in options:
        options['src'] = [ F.absfile(options['src']) ]
    options['o'] = F.absfile(options['o'])
    
    options['columns'] = U.tolist(options.get('columns', []))
    
    options['useLabel'] = 'barcode' not in options
    return options

def _testing(options):
    import evoware.fileutil as F
    options['i'] = F.testRoot('distribution.xls')
    options['o'] = F.testRoot('test.gwl')
    options['columns'] = ['buffer01']
    return options    

###########################
# MAIN
###########################
import evoware as E
TESTING = True

try:
    options = _defaultOptions()
    if TESTING:
        options = _testing(options)
    else:
        if len(sys.argv) < 2:
            _use( _defaultOptions() )
            
        options = U.cmdDict( _defaultOptions() )
    
    try:
        options = cleanOptions(options) 
    except KeyError, why:
        logging.error('missing option: ' + why)
        _use(options)
    
    xls = X.DistributionXlsReader(byLabel=options['useLabel'])
    xls.read(options['i'])

    reagents = xls.reagents
    
    if 'src' in options:
        srcxls = X.XlsReader(byLabel=options['useLabel'])
        srcxls.read( options['f'] )
        reagents = S.SampleList(srcxls.rows)
        
    columns = options['columns']
    
    converter = C.DistributionConverter(reagents=reagents, sourcefields=columns)
    
    targets = S.SampleList(xls.rows, converter=converter)
    
    with W.SampleWorklist(options['o'], reportErrors=options['dialogs']) as wl:
        wl.distributeSamples(targets)

except Exception, why:
    if options['dialogs']:
        D.lastException('Error generating Worklist')
    else:    
        raise
