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
    no matter how the code exits. If the with block exits through an
    exception, this exception will be reported to the user in an Error
    dialog box (can be switched off with Worklist(fname, reportErrors=False)).
    
    Alternatively, create the object in a normal fashion and call the close()
    method yourself:
    
    >>> wl = Worklist('outputfile.gwl')
        try:
            wl.A('src1', 1, 140)
            wl.D('dst1', 1, 140)
        finally:    
            wl.close()

    There are two properties:
    
    * f -- gives access to the writable file handle (a readonly property)
    
    * plateformat -- read or modify the number of wells per plate (default: 96)
                   this parameter is used to calculate positions and number
                   of wells in the transferColumn method

    Worklist methods -- overview:
    =============================
    
    aspirate -- generate a single aspirate line
    A -- shortcut expecting only labware, well and volume as parameters
    
    dispense -- generate a single dispense line
    D -- shortcut expecting only labware, well and volume (plus optional wash)
    
    transfer -- generate two lines (plus optional wash/tip change) for
                aspiration and dispense of the same volume
    
    transferColumn -- generate an aspirate and a dispense command for each
                      well in a given column
    
    wash -- insert wash / tip replacement statement
    flush -- insert flush statement
    B -- insert break statement (B)
    comment -- insert a comment
    
    write -- write a custom string to the worklist file
    
    Worklist examples:
    ==================
    
    >>> with Worklist('transfer_plate.gwl') as wl:

            for i in range(1,13):
                wl.transferColumn('plateSrc', i, 'plateDst', i, 120, wash=True)
    
            wl.B()
    
            wl.aspirate(rackLabel='Src1', position=1, volume=25)
            wl.dispense(rackLabel='Dst1', position=96, volume=25)
        
    The above example copies 120 ul from every well of every column of the 
    plate with labware label "plateSrc" to the same well in plate "plateDst".
    The tips are replaced after each dispense (W;).
    Afterwards, a break command is inserted (B;) and a single aspiration and
    dispense transfers 25 ul from plate Src1, A1 to plate Dst1, well H8; 
    again followed by a 'W;' command for tip replacement.
    
    These last two lines can be simplified to:
    >>> wl.A('Src1', 1, 25)
        wl.D('Dst1', 96, 25)
        
    A() and D() are "shortcuts" for the aspirate and dispense methods but only
    accept the three core label / position / volume parameters.
    
    These two lines can be further simplified to a single method call:
    >>> wl.transfer('Src1', 1, 'Dst1', 96, 25)
    
    ... which will generate the same two worklist commands plus the "wash" 
    (W;) command.
        
    'W;' is added by default, after each dispense command. This behaviour can
    be switched off by passing `wash=False` to dispense(), D(), or transfer().
    
    Wash and flush commands can be inserted manually by calling:
    >>> wl.wash()
    >>> wl.flush()
    
    Last not least, any other custom worklist command can be inserted as
    a raw string using the write method:
    >>> wl.write('C; This is a random comment')
    
    Worklist.write will check your input for line breaks, remove any of them
    and then add a standard line break as required by worklists. That means,
    you don't need to add a line break to the input string.
    
    
    """   

    ALLOWED_PLATES = [6, 12, 24, 96, 384, 1536]

    ## map plate format to 
    PLATE_ROWS = {6 : 2,
                  12: 3,
                  24: 4,
                  96: 8,
                  384: 16,
                  1536: 32}
    
   
    def __init__(self, fname, reportErrors=True):
        """
        @param fname - str, file name for output worklist (will be created)
        @param reportErrors - bool, report certain exceptions via dialog box
                              to user [True]
        """
        self.fname = F.absfile(fname)
        self._f = None  ## file handle
        self.reportErrors=reportErrors
        self._plateformat = 96
        self.rows = 8
        self.columns = 12
        
    def _get_file(self):
        if not self._f:
            try:
                self._f = open(self.fname, mode='w')
            except:
                if self.reportErrors: D.lastException()
                raise
        return self._f

    f = property(_get_file, doc='open file handle for writing')

    def _set_plateformat(self, wells=96):
        if not wells in self.ALLOWED_PLATES:
            raise WorklistException('plate format %r is not supported' % wells)
        self._plateformat = wells
        self.rows = self.PLATE_ROWS[wells]
        self.columns = wells / self.rows
        
    def _get_plateformat(self):
        return self._plateformat

    plateformat = property( _get_plateformat, _set_plateformat, 
                            doc='default plate format for column transfers')
    
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
    
    def transferColumn(self, srcLabel, srcCol, dstLabel, dstCol, 
                       volume,
                       liquidClass='', tipMask=None, wash=True):
        """
        Generate Aspirate commands for a whole plate column
        @param srcLabel - str, source rack label (on workbench)
        @param srcCol - int, column on source plate
        @param dstLabel - str, destination rack label (on workbench)
        @param dstCol - int, column on destination plate
        @param volume - int, aspiration / dispense volume
        @param liquidClass - str, alternative liquid class
        @param tipMask - int, alternative tip mask (1 - 128, 8 bit encoded)
        @param wash - bool, include 'W' statement for tip replacement after
                      dispense (default: True)
        
        @return n - int, number of aspiration / dispense pairs written
        """
        pos_src = (srcCol - 1) * self.rows + 1
        pos_dst = (dstCol - 1) * self.rows + 1
        
        for i in range(0, self.rows):
            self.aspirate(rackLabel=srcLabel, 
                          position=pos_src + i, 
                          volume=volume, 
                          liquidClass=liquidClass, tipMask=tipMask)
            self.dispense(rackLabel=dstLabel, 
                          position=pos_dst + i,
                          volume=volume,
                          liquidClass=liquidClass, tipMask=tipMask, 
                          wash=wash)
        return i
    
    def wash(self):
        """generate 'W;' wash / tip replacement command"""
        self.f.write('W;\n')
    
    def flush(self):
        """generate 'F;' tip flushing command"""
        self.f.write('F;\n')
        
    def B(self):
        """Generate break command forcing execution of all previous lines"""
        self.f.write('B;\n')
        
    def comment(self, comment):
        """Insert a work list comment"""
        self.write('C;' + comment)
    
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
        self.fname = F.testRoot('worklist_tmp.gwl')
    
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
    
    def test_worklist_highlevel(self):
        with Worklist(self.fname, reportErrors=False) as wl:
            wl.comment('Worklist generated by evoware.worklist.py')
            wl.transferColumn('src3', 2, 'dst3', 12, 120, wash=True)

    

if __name__ == '__main__':

    testing.localTest()
