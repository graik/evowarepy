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
"""
distribute.py -- Generate reagent distribution worklist from Excel file.

Syntax (non-interactive):
    distribute.py -i <distribute.xls> -o <output.worklist> 
                  [-barcode -src <sourcesamples.xls> -columns <name1 name2>]
                
Syntax (interactive):
    distribute.py -dialogs [-p <project directory>
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
              
    -barcode  interpret plate IDs in all tables as barcode ($Labware.ID$) 
              rather than labware label
    -columns  explicitely specify which source columns to process (default: all)

    -test     run built-in test case
    -debug    do not delete temporary files after running test

If -dialogs option is given, a missing -i or -o option will trigger a file open
dialog(s) for the appropriate file(s).

The position of reagents (plate or labware and well) can be specified 
in the same input (-i) excel file using the "reagent" keyword in the header. 
Or it can be specified in one or several additional source (-src) Excel files
using the regular "ID : (sub-ID) : plate : pos" column layout. 
"""

import sys, logging, os

import evoware.util as U
import evoware.fileutil as F
import evoware.dialogs as D

import evoware.sampleworklist as W
import evoware.samples as S
import evoware.excel as X
import evoware.sampleconverters as C

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
                            initialdir=options['p'], 
                            multiple=False, 
                            title="Distribution Table")
        
        if not 'o' in options:
            options['o'] = D.askForFile(defaultextension='*.gwl', 
                            filetypes=(('Evo Worklist','*.gwl'),
                                       ('Text file','*.txt'),
                                       ('All files','*.*')), 
                            initialdir=options['p'], 
                            multiple=False,
                            newfile=True,
                            title="Save Worklist output file as")
    
    
    options['i'] = F.existingFile(options['i'], cwd=cwd, 
                                  errmsg='Cannot find input (-i) file ')
    
    if 'src' in options:
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
def run( options ):
    try:
        try:
            options = cleanOptions(options) 
        except KeyError as why:
            logging.error('missing option: ' + str(why))
            U.scriptusage(options, doc=__doc__, force=True)
        
        xls = X.DistributionXlsReader(byLabel=options['useLabel'])
        xls.read(options['i'])
    
        reagents = xls.reagents
        
        if 'src' in options:
            for f in options['src']:
                srcxls = X.XlsReader(byLabel=options['useLabel'])
                srcxls.read( f )
                reagents.extend( S.SampleList(srcxls.rows) )
            
        columns = options['columns']
        
        converter = C.DistributionConverter(reagents=reagents, 
                                            sourcefields=columns)
        
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
    """Test distribute.py"""

    TAGS = [ testing.SCRIPT ]

    def prepare(self):
        """Called once"""
        import tempfile    
        self.f_project = tempfile.mkdtemp(prefix='evoware_distribute_')

    def cleanUp(self):
        """Called after all tests are done, except DEBUG==True"""
        import evoware.fileutil as F
        F.tryRemove(self.f_project, verbose=(self.VERBOSITY>1), tree=1)

    def generictest(self, options):
        import evoware.fileutil as F
        import os.path as O
                
        self.f_out = F.absfile(self.f_project + '/' + options['o'])
        
        run(options)
        
        self.assertTrue(O.exists(self.f_out))
        
        with open(self.f_out,'r') as f1, \
             open(F.testRoot('results/distribute.gwl'),'r') as f2:
            
            self.assertEqual(f1.readlines(), f2.readlines())
        

    def test_distribute(self):
        """distribute.py; distribution from single Excel file"""
        import evoware.fileutil as F
        
        options = {'i': F.testRoot('distribution.xls'), 
                   'o': 'distribute1.gwl', 
                   'p': self.f_project,
                   'columns': ['buffer01']        
                   }
        self.generictest(options)
        
    def test_distribute_sources(self):
        """distribute.py; distribution with seperate reagent source file"""
        import evoware.fileutil as F
        
        options = {'i': F.testRoot('distribution.xls'), 
                   'src': F.testRoot('distribution_sources.xls'),
                   'o': 'distribute2.gwl',
                   'p': self.f_project,
                   'columns': ['buffer01']        
                   }
        self.generictest(options)
        

if __name__ == '__main__':
    
    ## print usage and exit if there is less than 1 command line argument
    U.scriptusage(_defaultOptions(), doc=__doc__)  
    
    options = U.cmdDict(_defaultOptions())  ## parse commandline options
    
    if 'test' in options:
        testing.localTest(debug=('debug' in options))
        sys.exit(0)
    
    run(options)