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

"""Generate Evoware pipetting worklists"""

import fileutil as F
import dialogs as D

class WorklistException( Exception ):
    pass

class Worklist(object):
    """
    Basic Evoware worklist generator.
    
    Preferred usage is to wrap it in a ``with`` statement:
    
    >>> with Worklist('outputfile.gwl') as wl:
            wl. ... 
    
    This will ensure that the file handle is properly opened and closed,
    no matter how the code exits.
    
    Alternatively, create the object in a normal fashion and call the close()
    method yourself:
    
    >>> wl = Worklist('outputfile.gwl')
        try:
            wl. ...
        finally:    
            wl.close()
    """
    
    
    def __init__(self, fname):
        self.fname = F.absfile(fname)
        self._f = None  ## file handle
        
    def _get_file(self):
        if not self._f:
            self._f = open(self.fname, mode='w')
        return self._f

    f = property(_get_file, doc='open file handle')
    
    def close(self):
        """
        Close file handle. This method should be called automatically by 
        __del__ or the with statement.
        """
        if self._f:
            self._f.close()
            self._f = None
    
    def __enter__(self):
        """Context guard for entering with statement"""
        return self
    
    def __exit__(self, type, value, traceback):
        """Context guard for exiting with statement"""
        try:
            self.close()
        except:
            pass
        
        ## report last Exception to user
        if type:
            D.lastException()
    

if __name__ == '__main__':
    
    fname = 'testdata/worklist_tmp.gwl'
    
    with Worklist(fname) as wl:
        wl.f.write('test line 1')
        wl.f.write('test line 2')
    
    print wl._f