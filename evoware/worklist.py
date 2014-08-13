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
            wl.A('src1', 1, 140)
            wl.D('dst1', 1, 140)
    
    This will ensure that the file handle is properly opened and closed,
    no matter how the code exits.
    
    Alternatively, create the object in a normal fashion and call the close()
    method yourself:
    
    >>> wl = Worklist('outputfile.gwl')
        try:
            wl.A('src1', 1, 140)
            wl.D('dst1', 1, 140)
        finally:    
            wl.close()

    Worklist methods -- overview:
    =============================
    
    aspirate -- generate a single aspirate line
    A -- shortcut accepting only labware, well and volume
    
    dispense -- generate a single dispense line
    D -- shortcut accepting only labware, well and volume (plus optional wash)
    
    transfer -- generate two lines (plus optional wash/tip change) for
                aspiration and dispense of the same volume
    
    write -- write a custom string to the worklist file

    """   
    
    def __init__(self, fname, reportErrors=True):
        """
        @param fname - str, file name for output worklist (will be created)
        @param reportErrors - bool, report certain exceptions via dialog box
                              to user [True]
        """
        self.fname = F.absfile(fname)
        self._f = None  ## file handle
        self.reportErrors=reportErrors
        
    def _get_file(self):
        if not self._f:
            try:
                self._f = open(self.fname, mode='w')
            except:
                if self.reportErrors: D.lastException()
                raise
        return self._f

    f = property(_get_file, doc='open file handle for writing')
    
    def close(self):
        """
        Close file handle. This method will be called automatically by 
        __del__ or the with statement.
        """
        if self._f:
            self._f.close()
            self._f = None
    
    def __enter__(self):
        """Context guard for entering ``with`` statement"""
        return self
    
    def __exit__(self, type, value, traceback):
        """Context guard for exiting ``with`` statement"""
        try:
            self.close()
        except:
            pass
        
        ## report last Exception to user
        if type and self.reportErrors:
            D.lastException()
    
    def aspirate(self, rackLabel='', rackID='', rackType='', 
                 position=1, tubeID='', volume=0,
                 liquidClass='', tipMask=None):
        """
        Generate a single aspirate command. Required parameters are:
        @param rackLabel or rackID - str, source rack label or barcode ID
        @param position - int, well position (default:1)
        @param volume - int, volume in ul
        
        Optional parameters are:
        @param rackType - str, validate that rack has this type
        @param tubeID - str, tube bar code
        @param liquidClass - str, alternative liquid class
        @param tipMask - int, alternative tip mask (1 - 128, 8 bit encoded)
        """
        if not rackLabel or rackID:
            raise WorklistException, 'Specify either source rack label or ID.'
        
        tipMask = str(tipMask or '')
        
        r = 'A %s;%s;%s;%i;%s;%i;%s;%s\n' % (rackLabel, rackID, rackType, position,
                                    tubeID, volume, liquidClass, tipMask)
        
        self.f.write(r)
    
    def A(self, rackLabel, position, volume):
        """
        aspirate shortcut with only the three core parameters
        @param rackLabel - str, source rack label (on workbench)
        @param position - int, source well position
        @param volume - int, aspiration volume
        """
        self.aspirate(rackLabel=rackLabel, position=position, volume=volume)

    
    def dispense(self, rackLabel='', rackID='', rackType='', 
                 position=1, tubeID='', volume=0,
                 liquidClass='', tipMask=None, wash=True):
        """
        Generate a single dispense command. Required parameters are:
        @param rackLabel or rackID - str, source rack label or barcode ID
        @param position - int, well position (default:1)
        @param volume - int, volume in ul
        
        Optional parameters are:
        @param rackType - str, validate that rack has this type
        @param tubeID - str, tube bar code
        @param liquidClass - str, alternative liquid class
        @param tipMask - int, alternative tip mask (1 - 128, 8 bit encoded)
        
        Tip-handling:
        @param wash - bool, include 'W' statement for tip replacement after
                      dispense (default: True)
        """
        if not rackLabel or rackID:
            raise WorklistException, 'Specify either destination rack label or ID.'
        
        tipMask = str(tipMask or '')
        
        r = 'D %s;%s;%s;%i;%s;%i;%s;%s\n' % (rackLabel, rackID, rackType, position,
                                    tubeID, volume, liquidClass, tipMask)
        
        self.f.write(r)
        
        if wash:
            self.f.write('W;\n')
    
    def D(self, rackLabel, position, volume, wash=True):
        """
        dispense shortcut with only the three core parameters
        @param rackLabel - str, destination rack label (on workbench)
        @param position - int, destination well position
        @param volume - int, aspiration volume
        @param wash - bool, include 'W' statement for tip replacement after
                      dispense (default: True)
        """
        self.dispense(rackLabel=rackLabel, position=position, volume=volume,
                      wash=wash)
    
    def transfer(self, srcLabel, srcPosition, dstLabel, dstPosition, volume,
                 wash=True):
        """
        @param srcLabel - str, source rack label (on workbench)
        @param srcPosition - int, source well position
        @param dstLabel - str, destination rack label (on workbench)
        @param dstPosition - int, destination well position
        @param volume - int, aspiration volume
        @param wash - bool, include 'W' statement for tip replacement after
                      dispense (default: True)
        """
        self.A(srcLabel, srcPosition, volume)
        self.D(dstLabel, dstPosition, volume, wash=wash)
    
    def write(self, line):
        """
        Directly write a custom line to worklist. A line break is added 
        automatically (i.e. don't add it to the input).
        """
        line.replace('\n', '')
        line.replace('\r', '')
        
        self.f.write(line + '\n')
    
######################
### Module testing ###
import testing

class Test(testing.AutoTest):
    """Test Worklist"""

    TAGS = [ testing.NORMAL ]

    def prepare( self ):
        self.fname = F.test('worklist_tmp.gwl')
    
    def test_createWorklist( self ):
        with Worklist(self.fname) as wl:
            wl.f.write('test line 1')
            wl.f.write('test line 2')

        self.assertEqual(wl._f, None)

    def test_worklistFileError( self ):
        
        def inner_call():
            with Worklist('', reportErrors=self.local) as wl:
                wl.f.write('test line 1')
                wl.f.write('test line 2')

        self.assertRaises(IOError, inner_call)
    
    def test_gwl_aspirate_dispense( self ):
        with Worklist(self.fname, reportErrors=False) as wl:
            for i in range(8):
                wl.aspirate(rackLabel='Src1', position=i+1, volume=25)
                wl.dispense(rackLabel='dst1', position=i+1, volume=25)
            
            for i in range(8):
                wl.A('src2', i+1, 100)
                wl.D('dst2', i+1, 100)
            
            for i in range(96):
                wl.transfer('src3', i+1, 'dst3', i+1, 150, wash=False)
    

if __name__ == '__main__':

    testing.localTest()
