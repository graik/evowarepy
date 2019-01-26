#!/usr/bin/env python
##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2019 Raik Gruenberg
"""Protoype script for generating PCR setup worklist from Excel files"""

import sys, logging

import evoware.util as U
import evoware.fileutil as F
import evoware.dialogs as D

import evoware.sampleworklist as W
import evoware.samples as S
import evoware.sampleconverters as C
import evoware.excel as X

def _use( options ):
    print("""
combine.py -- Combine (hit-picking) samples from various positions

Syntax (non-interactive):
    distribute.py -i <reactions.xls> -o <output.worklist> 
                  -src <sources.xls>
                  [-barcode -columns <name1 name2>]
                
Syntax (interactive):
    pcrsetup.py -dialogs [-p <project directory>
                -o <output.worklist> -i <reactions.xls> -src <sources.xls>
                -barcode]


Options:
    -dialogs  generate file open dialogs for any missing input files
              This option also activates user dialog-based error reporting.
    -p        default project directory for input and output files
    
    -i        input excel file listing listing which source constructs should be pipetted
              into which target wells
    -src      source samples and their positions
    -o        output file name for generated worklist
              
    -barcode  interpret plate IDs in all tables as barcode ($Labware.ID$) 
              rather than labware label
    -columns  explicitely specify which source columns to process (default: all)

If -dialogs is given, a missing -i or -o option triggers a file open
dialog(s) for the appropriate file(s).

Currently defined options:
""")
    for key, value in options.items():
        print("\t-",key, "\t",value)

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
    
    options['columns'] = U.tolist(options.get('columns', []))
    
    options['useLabel'] = 'barcode' not in options
    return options

###########################
# MAIN
###########################
import evoware as E

import evoware.fileutil as F

TESTING = True

try:

    options = _defaultOptions()
    if not TESTING:
        if len(sys.argv) < 2:
            _use( _defaultOptions() )
            
        options = U.cmdDict( _defaultOptions() )
    else:    
        ## TESTING
        options['i'] = F.testRoot('targetlist_PCR.xls')
        options['src'] = [ F.testRoot('primers.xls'), F.testRoot('partslist.xls')]
        options['o'] = F.testRoot('/tmp/evoware_test.gwl')
        options['columns'] = ['primer1', 'primer2', 'template']    
    
    try:
        options = cleanOptions(options) 
    except KeyError as why:
        logging.error('missing option: ' + why)
        _use(options)
    
    srcsamples = S.SampleList()
    
    for f in options['src']:
        srcxls = X.XlsReader(byLabel=options['useLabel'])
        srcxls.read( f )
        srcsamples += S.SampleList(srcxls.rows)
        
    xls = X.DistributionXlsReader(byLabel=options['useLabel'])
    xls.read(options['i'])
    
    srcsamples += xls.reagents

    columns = options['columns']
    converter = C.DistributionConverter(reagents=srcsamples, sourcefields=columns)
    
    targets = S.SampleList(xls.rows, converter=converter)
    
    with W.SampleWorklist(options['o'], reportErrors=options['dialogs']) as wl:
        wl.distributeSamples(targets)

except Exception as why:
    if options['dialogs']:
        D.lastException('Error generating Worklist')
    else:    
        raise
