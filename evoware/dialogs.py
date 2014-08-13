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

"""TK / Windows user-notifications and dialog boxes"""

import Tkinter, tkFileDialog, tkMessageBox
import sys, traceback, inspect
import os

import fileutil as F

## create package-wide hidden window for unattached dialog boxes
root = Tkinter.Tk()
root.withdraw()

class PyDialogError(Exception):
    pass

## see: http://stackoverflow.com/questions/9319317/quick-and-easy-file-dialog-in-python
def askForFile(defaultextension='*.csv', 
               filetypes=(('Comma-separated values (CSV)', '*.csv'),
                          ('Text file', '*.txt'),
                          ('All files', '*.*')), 
               initialdir='', 
               initialfile='', 
               multiple=False, 
               title=None):
    """present simple Open File Dialog to user and return selected file."""
    options = dict(defaultextension=defaultextension, 
               filetypes=filetypes,
               initialdir=initialdir, 
               initialfile=initialfile, 
               multiple=multiple, 
               title=title)
    
    r = tkFileDialog.askopenfilename(**options)
    return r

def info(title, message):
    """Display info dialog box to user"""
    tkMessageBox.showinfo(title, message)

def warning(title, message):
    """Display warning dialog box to user"""
    tkMessageBox.showwarning(title, message)

def error(title, message):
    """Display error dialog box to user"""
    tkMessageBox.showerror(title, message)

def lastException():
    """Report last exception in a dialog box."""
    msg = __lastError()
    tkMessageBox.showerror(title='Python Exception', message=msg)

def __lastError():
    """
    Collect type and line of last exception.
    
    @return: '<ExceptionType> raised in line <lineNumber>. Reason: <Exception arguments>'
    @rtype: String
    """
    error, value, trace = sys.exc_info()
    if not error:
        return ''

    file = inspect.getframeinfo( trace.tb_frame )[0]
    try:
        error = error.__name__
        file = os.path.basename(file)
    except:
        pass

    r = "%s\nraised in %s line %i.\n\nReason: %s." % ( str(error),
                                          file, trace.tb_lineno, str(value) )

    return r



######################
### Module testing ###
import testing

class Test(testing.AutoTest):
    """Test dialogs"""

    TAGS = [ testing.NORMAL ]

    def prepare( self ):
        pass
    
    def test_askForFile( self ):
        """fileutil.askForFile test"""
        r = askForFile(title='Test File')
        self.assertNotEqual(r, 'test.dat')
    
    def test_info(self):
        info('testInfo', 'This is a test.')
    
    def test_warning(self):
        warning('testWarning', 'This is a warning.')

    def test_error(self):
        error('testError', 'This is an error.')
    
    def test_exception(self):
        try:
            raise PyDialogError, 'testing'
        except PyDialogError, what:
            lastException()

if __name__ == '__main__':

    testing.localTest()

