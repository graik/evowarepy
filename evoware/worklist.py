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

"""Generate Evoware pipetting worklists"""

__all__ = ['Worklist', 'WorklistException']  ## result of `import *`

from . import fileutil as F
from . import dialogs as D
from . import plate as P

class WorklistException( Exception ):
    pass

class Worklist(object):
    """
    Low-level Evoware worklist generator.
    
    Preferred usage is to wrap it in a ``with`` statement::
    
        with Worklist('outputfile.gwl') as wl:
            wl.A('src1', 1, 140)
            wl.D('dst1', 1, 140)
    
    This will ensure that the file handle is properly opened and closed, no
    matter how the code exits. If the with block exits through an exception,
    this exception will be reported to the user in an Error dialog box (can
    be switched off with ``Worklist(fname, reportErrors=False)``).
    
    Alternatively, create the object in a normal fashion and call the close()
    method yourself::
    
        wl = Worklist('outputfile.gwl')
        try:
            wl.A('src1', 1, 140)
            wl.D('dst1', 1, 140)
        finally:    
            wl.close()

    The file (handle) will be created and opened only with the first ``write`` 
    statement (``wl.A()`` in the above example).
    
    **Properties:**
    
        * `f` -- gives access to the writable file handle (a readonly property,
          first access will automatically create and open the file)
    
    **Methods:**
    
        * :func:`~evoware.worklist.Worklist.aspirate` -- generate A single aspirate line
        * :any:`A()` -- shortcut expecting only labware, well and volume as parameters
    
        * `dispense()` -- generate a single dispense line
        * `D()` -- shortcut expecting only labware, well and volume (plus optional wash)
    
        * `distribute()` -- generate a reagent distribute command (R)
    
        * `transfer()` -- generate two lines (plus optional wash/tip change) for
          aspiration and dispense of the same volume
                
        * `transferColumn()` -- generate an aspirate and a dispense command for each
          well in a given column (Note: replace this by R?)
    
        * `wash()` -- insert wash / tip replacement statement
        * `flush()` -- insert flush statement
        * `B()` -- insert break statement (B)
        * `comment()` -- insert a comment
    
        * `write()` -- write a custom string to the worklist file
    
    **Examples:**
        ::
        
            with Worklist('transfer_plate.gwl') as wl:
    
                for i in range(1,13):
                    wl.transferColumn('plateSrc', i, 'plateDst', i, 120, wash=True)
        
                wl.B()
        
                wl.aspirate(rackLabel='Src1', position=1, volume=25)
                wl.dispense(rackLabel='Dst1', position=96, volume=25)
            
        The above example copies 120 ul from every well of every column of the
        plate with labware label "plateSrc" to the same well in plate "plateDst".
        The tips are replaced after each dispense (W;). Afterwards, a break
        command is inserted (B;) and a single aspiration and dispense transfers
        25 ul from plate Src1, A1 to plate Dst1, well H8; again followed by a
        'W;' command for tip replacement.
        
        These last two lines can be simplified to::
        
            wl.A('Src1', 1, 25)
            wl.D('Dst1', 96, 25)
            
        `A()` and `D()` are "shortcuts" for the `aspirate` and `dispense` methods
        but only accept the three core label / position / volume parameters.
        
        These two lines can be further simplified to a single method call:
        
        >>> wl.transfer('Src1', 1, 'Dst1', 96, 25)
        
        ... which will generate the same two worklist commands plus the "wash" 
        (W;) command.
            
        'W;' is added by default, after each dispense command. This behaviour can
        be switched off by passing ``wash=False`` to `dispense()`, `D()`, or
        `transfer()`.
    
    **Other methods:**
   
        Wash and flush commands can be inserted manually by calling:
        
        >>> wl.wash()
        >>> wl.flush()
        
        Comments can be added like this:
        
        >>> wl.comment('This is a comment')
        
        ... which results in a worklist line: "C; This is a comment"
        
        Last not least, any other custom worklist command can be inserted as
        a raw string using the `write` method:
        
        >>> wl.write('C; This is a random comment')
        
        `Worklist.write` will check your input for line breaks, remove any of them
        and then add a standard line break as required by worklists. That means,
        you don't need to add a line break to the input string.
    """    
   
    def __init__(self, fname, reportErrors=True):
        """
        Worklist constructor.
            >>> wl = Worklist('outputfile.gwl')
            
        Args:
            fname (str): file name for output worklist (will be created)
            reportErrors (bool): report exceptions via dialog box to user [True]
        """
        self.fname = F.absfile(fname)
        self._f = None  ## file handle
        self.reportErrors=reportErrors
        
    def __str__(self):
        return 'Worklist in %s' % self.fname
        
    def _get_file(self):
        if not self._f:
            try:
                self._f = open(self.fname, mode='w')
            except:
                if self.reportErrors: D.lastException()
                raise
        return self._f

    f = property(_get_file, doc='property giving file handle for writing')

    
    def close(self):
        """
        Close file handle. This method will be called automatically by 
        ``__del__`` or the ``with`` statement.
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
    
    def aspirate(self, rackID='', rackLabel='', rackType='', 
                 position=1, tubeID='', volume=0,
                 liquidClass='', tipMask=None):
        """
        Generate a single aspirate command. Required parameters:
        
        Keyword Args:
            rackID (str): source rack barcode
            rackLabel (str): source rack label (give either rackID or rackLabel)
            position (int): well position (default:1)
            volume (int): volume in ul
        
        The following parameters are optional:
        
        Keyword Args:
            rackType (str): validate that rack has this type (required for ``rackID``)
            tubeID (str): tube bar code
            liquidClass (str): alternative liquid class
            tipMask (int): alternative tip mask (1 - 128, 8 bit encoded)
        """
        if not (rackLabel or (rackID and rackType)):
            raise WorklistException('Specify either source rack label, or both ID (barcode) and rackType.')
        
        tipMask = str(tipMask or '')
        
        r = 'A;%s;%s;%s;%i;%s;%i;%s;%s;\n' % (rackLabel, rackID, rackType, position,
                                    tubeID, volume, liquidClass, tipMask)
        
        self.f.write(r)
    
    def A(self, rackID, position, volume, byLabel=False, rackType=''):
        """
        aspirate shortcut with only the three core parameters

        Args:
            rackID (str): source labware ID (or rack ID if labware lacks ID)
            position (int): source well position
            volume (int): aspiration volume
        
        Keyword Args:
            byLabel (bool): use rack label instead of labware / rack ID
            rackType (str): labware type, required when using ID
        """
        if not byLabel:
            self.aspirate(rackID=rackID, position=position, volume=volume,
                          rackType=rackType)
        else:
            self.aspirate(rackLabel=rackID, position=position, volume=volume)

    
    def dispense(self, rackID='', rackLabel='', rackType='', 
                 position=1, tubeID='', volume=0,
                 liquidClass='', tipMask=None, wash=True):
        """
        Generate a single dispense command.
        
        Keyword Args:
            rackLabel or rackID (str): source rack label or barcode ID
            position (int): well position (default:1)
            volume (int): volume in ul
        
        The following parameters are optional.
        
        Keyword Args:
            rackType (str): validate that labware has this type
            tubeID (str): tube bar code
            liquidClass (str): alternative liquid class
            tipMask (int): alternative tip mask (1 - 128, 8 bit encoded)
        
            wash (bool): include 'W' statement for tip replacement after
                 dispense (default: True)
        """
        if not (rackLabel or (rackID and rackType)):
            raise WorklistException('Specify either destination rack label or both ID and rack type.')
        
        tipMask = str(tipMask or '')
        
        r = 'D;%s;%s;%s;%i;%s;%i;%s;%s;\n' % (rackLabel, rackID, rackType, position,
                                    tubeID, volume, liquidClass, tipMask)
        
        self.f.write(r)
        
        if wash:
            self.f.write('W;\n')
    
    def D(self, rackID, position, volume, wash=True, byLabel=False, rackType=''):
        """
        dispense shortcut with only the three core parameters
        
        Args:
            rackID (str): dest. labware ID (or rack ID if labware lacks ID)
            position (int): destination well position
            volume (int): aspiration volume
        
        Keyword Args:
            wash (bool): include 'W' statement for tip replacement after
                    dispense (default: True)
            byLabel (bool): use rack label instead of labware/rack ID [False]
            rackType (str): labware type, required when using ID
        """
        if not byLabel:
            self.dispense(rackID=rackID, position=position, volume=volume,
                          wash=wash, rackType=rackType)
        else:
            self.dispense(rackLabel=rackID, position=position, volume=volume,
                          wash=wash)

    def distribute(self, srcRackID='', srcRackLabel='', srcRackType='', 
                   srcPosStart=1, srcPosEnd=96,
                   dstRackID='', dstRackLabel='', dstRackType='', 
                   dstPosStart=1, dstPosEnd=96,
                   volume=0, liquidClass='',
                   nDitiReuses=1, nMultiDisp=1, direction=0,
                   excludeWells=[] ):
        """
        Generate a Reagent Distribution command (R). 
        
        Keyword Args:
            srcRackID (str): source barcode (either scrRackID or scrRackLabel
              is required)
            srcRackLabel (str): source rack label
            srcPosStart (int): source starting well position (default:1)
            srcPosEnd (int): source ending well position (default:96)
    
            dstRackID (str): destination barcode (either this or dstRackLabel 
              is required)
            dstRackLabel (str): destination rack label
            dstPosStart (int): destination starting well position (default:1)
            dstPosEnd (int): destination ending well position (default:96)

            volume (int): volume in ul (required)
        
            srcRackType (str): validate that source rack has this type
            dstRackType (str): validate that destination rack has this type
            liquidClass (str): alternative liquid class
            
            nDitiReuses (int): (default:1, no DiTi re-use)
            nMultiDisp (int): (default:1, no multi-dispensing)
            direction (int): pipetting direction (default:0 from left to right)
            
            exlcudeWells ([int]): list of destination wells to skip []
        """
        if not (srcRackLabel or (srcRackID and srcRackType)):
            raise WorklistException('Specify either source rack label or ID + rack type.')
        if not (dstRackLabel or (dstRackID and dstRackType)):
            raise WorklistException('Specify either destination rack label or ID + rack type.')
        
        r = 'R;%s;%s;%s;%i;%i;' % (srcRackLabel, srcRackID, srcRackType, 
                                    srcPosStart, srcPosEnd)
        r+= '%s;%s;%s;%i;%i;' % (dstRackLabel, dstRackID, dstRackType, 
                                 dstPosStart, dstPosEnd)
        
        r+= '%i;%s;%i;%i;%i;' % (volume, liquidClass, nDitiReuses, nMultiDisp,
                                direction)
        
        if excludeWells:
            r += ';'.join([str(x) for x in excludeWells])
        
        r+= '\n'
        
        self.f.write(r)
        
    
    def transfer(self, srcID, srcPosition, dstID, dstPosition, volume,
                 wash=True, byLabel=False, srcRackType='', dstRackType=''):
        """
        Args:
            srcID (str): source labware ID (or rack label if missing)
            srcPosition (int): source well position
            dstID (str): destination labware ID (or rack label if missing)
            dstPosition (int): destination well position
            volume (int): aspiration volume
        
        Keyword Args:
            wash (bool): include 'W' statement for tip replacement after
                   dispense (default: True)
            byLabel (bool): use rack label instead of labware/rack ID [False]
            srcRackType (str): labware type, required when byLabel==False
            dstRackType (str): labware type, required when byLabel==False
        """
        self.A(srcID, srcPosition, volume, byLabel=byLabel, rackType=srcRackType)
        self.D(dstID, dstPosition, volume, wash=wash, byLabel=byLabel, 
               rackType=dstRackType)
  
    
    def transferColumn(self, srcID, srcCol, dstID, dstCol, 
                       volume, plateformat=P.PlateFormat(96),
                       liquidClass='', tipMask=None, wash=True, 
                       byLabel=False, srcRackType='', dstRackType=''):
        """
        Generate Aspirate & Dispense commands for a whole plate column
        
        Args:
            srcID (str): source labware ID (or rack label)
            srcCol (int): column on source plate
            dstID (str): destination labware ID (or rack label)
            dstCol (int): column on destination plate
            volume (int): aspiration / dispense volume
            
        Keyword Args:
            plateformat (PlateFormat, default: 96-well layout
            liquidClass (str): alternative liquid class
            tipMask (int): alternative tip mask (1 - 128, 8 bit encoded)
            wash (bool): include 'W' statement for tip replacement after
                   dispense (default: True)
            byLabel (bool): use rack label instead of labware/rack ID [False]
            srcRackType (str): labware type, required when byLabel==False
            dstRackType (str): labware type, required when byLabel==False
        
        Returns:
            int: number of aspiration / dispense pairs written
        """
        rows = plateformat.ny
        pos_src = (srcCol - 1) * rows + 1
        pos_dst = (dstCol - 1) * rows + 1
        
        if byLabel:
            srcRack = {'rackLabel':srcID}
            dstRack = {'rackLabel':dstID}
        else:
            srcRack = {'rackID':srcID, 'rackType':srcRackType}
            dstRack = {'rackID':dstID, 'rackType':dstRackType}
        
        for i in range(0, rows):
            self.aspirate(position=pos_src + i, 
                          volume=volume, 
                          liquidClass=liquidClass, tipMask=tipMask,
                          **srcRack)
            self.dispense(position=pos_dst + i,
                          volume=volume,
                          liquidClass=liquidClass, tipMask=tipMask, 
                          wash=wash,
                          **dstRack)
        return i
    
    
    def multidiswithflush(self, srcLabel='', srcPos=1, dstLabel='', dstPos=[], 
                          volume=0, tipVolume=900, liquidClass='', tipMask=None, 
                          wash=True, flush=True):
        """
        Args:
            wash (bool): replace tip *after* all multi-dispense actions.
        """
        n_dispense = len(dstPos)
        totalVolume = volume * n_dispense
        tipVolume = tipVolume - tipVolume % volume  # reduce tip volume to nearest multiple of dispense volume
        
        dstPos.reverse() # first entry is last now
        
        while totalVolume > 0:
            aspVolume = totalVolume if totalVolume <= tipVolume else tipVolume
        
            self.aspirate(rackLabel=srcLabel, 
                            position=srcPos, 
                            volume=aspVolume, 
                            liquidClass=liquidClass, tipMask=tipMask)
            
            n_next_dispense = int(aspVolume / volume)
            
            assert n_next_dispense <= len(dstPos), 'missmatch between aspiration volume and dispense actions left'
            
            for i in range(0, n_next_dispense):
                
                well = dstPos.pop()
                
                self.dispense(rackLabel=dstLabel, 
                              position=well,
                              volume=volume,
                              liquidClass=liquidClass, tipMask=tipMask, 
                              wash=False)
                
            totalVolume = totalVolume - aspVolume
            
            if totalVolume > 0 and flush:
                self.flush()
            
        if wash:
            self.wash()
    
    
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
        self.write('C; ' + comment)
    
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
import testing, tempfile

class Test(testing.AutoTest):
    """Test Worklist"""

    TAGS = [ testing.NORMAL ]

    def setUp( self ):
        """Called before *each* test"""
        self.fname = tempfile.mktemp(suffix=".gwl", prefix='test_worklist_')
    
    def tearDown(self):
        """Called after *each* test"""
        if not self.DEBUG:
            F.tryRemove(self.fname, verbose=self.DEBUG)
    
    def test_createWorklist( self ):
        with Worklist(self.fname) as wl:
            wl.f.write('test line 1')
            wl.f.write('test line 2')

        self.assertEqual(wl._f, None)

    def test_worklistFileError( self ):
        
        def inner_call():
            with Worklist('', reportErrors=False) as wl:
                wl.f.write('test line 1')
                wl.f.write('test line 2')

        self.assertRaises(IOError, inner_call)
    
    def test_gwl_aspirate_dispense( self ):
        with Worklist(self.fname, reportErrors=False) as wl:
            for i in range(8):
                wl.aspirate(rackLabel='Src1', position=i+1, volume=25)
                wl.dispense(rackLabel='dst1', position=i+1, volume=25)
            
            for i in range(8):
                wl.A('src2', i+1, 100, byLabel=True)
                wl.D('dst2', i+1, 100, rackType='microplate, landscape')
            
            for i in range(96):
                wl.transfer('src3', i+1, 'dst3', i+1, 150, wash=False, 
                            byLabel=True)
                wl.transfer('src10001', i+1, 'dst30001', i+1, 150, wash=False, 
                            srcRackType='microplate, landscape',
                            dstRackType='microplate, landscape')
    
    def test_worklist_highlevel(self):

        with Worklist(self.fname, reportErrors=False) as wl:
            wl.comment('Worklist generated by evoware.worklist.py')
            wl.transferColumn('src3', 2, 'dst3', 12, 120, wash=True, 
                              byLabel=True)
            wl.transferColumn('src3', 2, 'dst3', 12, 120, wash=True, 
                              byLabel=False, srcRackType='microplate',
                              dstRackType='microplate')
            
            wl.comment('worklist.distribute example')
            wl.distribute(srcRackLabel='src1', srcPosStart=1, srcPosEnd=8,
                          dstRackLabel='dst1', dstPosStart=1, dstPosEnd=96,
                          volume=100, 
                          nDitiReuses=2, nMultiDisp=12, 
                          excludeWells=[1,96] )


if __name__ == '__main__':

    testing.localTest()
