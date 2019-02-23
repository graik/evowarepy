#!/usr/bin/env python
##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2019 Raik Gruenberg
"""
cherrypick.py -- Combine (hit-picking) samples from various positions

Syntax (non-interactive):
    cherrypick.py -i <reactions.xls> -o <output.worklist> 
                  -src <sources.xls>
                  [-barcode -columns <name1 name2>]
                
Syntax (interactive):
    cherrypick.py -dialogs [-p <project directory>
                -o <output.worklist> -i <reactions.xls> -src <sources.xls>
                -barcode]


Options:
    -dialogs  generate file open dialogs for any missing input files
              This option also activates user dialog-based error reporting.
    -p        default project directory for input and output files
    
    -i        input excel file listing target samples and which source samples 
              (IDs) should be cherry-picked into each of them
    -src      source samples and their positions
    -o        output file name for generated worklist
              
    -barcode  interpret plate IDs in all tables as barcode ($Labware.ID$) 
              rather than labware label
    -columns  explicitely specify which source columns to process (default: all)

    -test     run built-in test case
    -debug    do not delete temporary files after running test

If -dialogs is given, a missing -i, -src or -o option triggers a file open
dialog(s) for the appropriate file(s).
"""

import sys, logging

import evoware.util as U
import evoware.fileutil as F
import evoware.dialogs as D

import evoware.sampleworklist as W
import evoware.samples as S
import evoware.sampleconverters as C
import evoware.excel as X
import evoware.fileutil as F

def _defaultOptions():
    return {}

def cleanOptions( options ):
    options['dialogs'] = 'dialogs' in options
    cwd = options.get('p',None)
    
    if options['dialogs']:
        
        if not 'i' in options:
            options['i'] = D.askForFile(defaultextension='*.xls', 
                            filetypes=(('Excel classic','*.xls'),
                                       ('Excel','*.xlsx'),('All files','*.*')), 
                            initialdir=cwd, 
                            multiple=False, 
                            title="Cherrypicking Table")
        
        if not 'src' in options:
            options['src'] = D.askForFile(defaultextension='*.xls', 
                                filetypes=(('Excel classic','*.xls'),
                                           ('Excel','*.xlsx'),
                                           ('All files','*.*')), 
                                initialdir=cwd, 
                                multiple=True, 
                                title="Source samples and their locations")

        if not 'o' in options:
            options['o'] = D.askForFile(defaultextension='*.gwl', 
                            filetypes=(('Evo Worklist','*.gwl'),
                                       ('Text file','*.txt'),
                                       ('All files','*.*')), 
                            initialdir=cwd, 
                            multiple=False,
                            newfile=True,
                            title="Save Worklist output file as")
    
    
    options['i'] = F.existingFile(options['i'], cwd=cwd,
                        errmsg='Cannot find cherrypicking input (-i) file.')

    options['src'] = U.tolist(options['src'])
    msg = 'Cannot find source (-src) file '
    options['src'] = [ F.existingFile(f, cwd=cwd, errmsg=msg)
                       for f in options['src'] ]

    options['o'] = F.absfile(options['o'], cwd=cwd)
    
    options['columns'] = U.tolist(options.get('columns', []))
    
    options['useLabel'] = 'barcode' not in options
    return options

#####################################
# MAIN Method (also used for testing)
#####################################

def run(options):
        
    try:    
        try:
            options = cleanOptions(options) 
        except KeyError as why:
            logging.error('missing option: ' + str(why))
            U.scriptusage(options, doc=__doc__, force=True)
        
        srcsamples = S.SampleList()
        
        for f in options['src']:
            srcxls = X.XlsReader(byLabel=options['useLabel'])
            srcxls.read( f )
            srcsamples += S.SampleList(srcxls.rows)
            
        xls = X.DistributionXlsReader(byLabel=options['useLabel'])
        xls.read(options['i'])
        
        srcsamples += xls.reagents
    
        columns = options['columns']
        converter = C.PickingConverter(sourcesamples=srcsamples, 
                                       sourcefields=columns,
                                       defaultvolumes=xls.volumes,
                                       relaxed_id=True,
                                       )
        
        targets = S.SampleList(xls.rows, converter=converter)
        
        with W.SampleWorklist(options['o'], 
                              reportErrors=options['dialogs']) as wl:
            wl.distributeSamples(targets)
    
    except Exception as why:
        if options['dialogs']:
            D.lastException('Error generating Worklist')
        else:
            logging.error(U.lastError())
            raise

######################
# Script test fixture
######################
from evoware import testing

class Test(testing.AutoTest):
    """Test cherrypick.py"""

    TAGS = [ testing.SCRIPT ]

    def prepare(self):
        """Called before every single test"""
        import tempfile    
        import evoware
        self.f_project = tempfile.mkdtemp(prefix='evoware_cherrypick_')
        evoware.plates.clear()


    def cleanUp(self):
        """Called after every individual test, except DEBUG==True"""
        import evoware.fileutil as F
        F.tryRemove(self.f_project, verbose=(self.VERBOSITY>1), tree=1)


    def generictest(self, options, expected='results/cherrypick_simple.gwl'):
        import evoware.fileutil as F
        import os.path as O
                
        self.f_out = F.absfile(self.f_project + '/' + options['o'])
        
        run(options)
        
        self.assertTrue(O.exists(self.f_out))
        
        with open(self.f_out,'r') as f1, open(F.testRoot(expected),'r') as f2:
            
            self.assertEqual(f1.readlines(), f2.readlines())
        

    def test_cherrypick_simple(self):
        """cherrypick.py; cherrypicking from Excel files"""
        import evoware.fileutil as F
        
        options = {'i': F.testRoot('targetlist_PCR.xls'), 
                   'src': [F.testRoot('primers.xls'), 
                           F.testRoot('partslist_simple.xls')],
                   'o': 'cherrypicking_simple.gwl',
                   'p': self.f_project,
                   'columns' : ['primer1', 'primer2', 'template']
                   }
        self.generictest(options)
        

    def test_cherrypick_flexibleIDs(self):
        """cherrypick.py; cherrypicking with flexible sub-ID handling"""
        import evoware.fileutil as F
        
        options = {'i': F.testRoot('targetlist_PCR.xls'), 
                   'src': [F.testRoot('primers.xls'), 
                           F.testRoot('partslist.xls')],
                   'o': 'cherrypicking_flexible.gwl',
                   'p': self.f_project,
                   'columns' : ['primer1', 'primer2', 'template']
                   }
        self.generictest(options, 'results/cherrypick_flexible.gwl')
      
if __name__ == '__main__':
    
    ## print usage and exit if there is less than 1 command line argument
    U.scriptusage(_defaultOptions(), doc=__doc__)  
    
    options = U.cmdDict(_defaultOptions())  ## parse commandline options
    
    if 'test' in options:
        testing.localTest(debug=('debug' in options))
        sys.exit(0)
    
    run(options)