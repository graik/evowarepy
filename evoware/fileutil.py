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

"""General purpose methods; mostly about file handling"""

import os.path as osp
import os
import shutil, glob, sys

import logging

from evoware import util

class UtilError( Exception ):
    pass


def absfile( filename, resolveLinks=True, cwd=None ):
    """
    Get absolute file path::
      - expand ~ to user home, change
      - expand ../../ to absolute path
      - resolve links
      - add working directory to unbound files ('ab.txt'->'/home/raik/ab.txt')

    Args:
        filename (str): name of file
        resolveLinks (1|0): eliminate any symbolic links (default: 1)
        cwd (str): alternative current working directory to use for non-absolute
            input file/path names (defaults to actual current workking dir)
    
    Returns: 
        str: absolute path or filename

    Raises: UtilError: if a ~user part does not translate to an existing path
    """
    if not filename:
        return filename
    
    r = osp.expanduser(filename)
    if cwd and not osp.isabs(r):
        r = osp.join(cwd,r)
    
    r = osp.abspath(r)

    if '~' in r:
        raise UtilError('Could not expand user home in %s' % filename)

    if resolveLinks:
        r = osp.realpath( r )
    return r

def existingFile(filename:str, cwd:str=None, resolve:bool=True, errmsg:str=''):
    """
    Convert input filename to absolute path and verify existence of that file.
    
    Args:
        filename (str): name of file
        cwd (str): alternative current working directory to use for non-absolute
            input file/path names (defaults to actual current workking dir)
        resolve (bool): eliminate any symbolic links (default: True)
        errmsg (str): alternative error message if file is not found
    
    Returns:
       str: absolute path or filename (see also `absfile`)
       
    Raises:
       UtilError: if a ~user part does not translate to an existing user or path
       FileNotFoundError: if the file does not exist 
    """
    r = absfile(filename, resolveLinks=resolve, cwd=cwd)
    
    if not osp.exists(r):
        msg = errmsg or 'Cannot find file: '
        raise FileNotFoundError(msg + r)
    
    return r


def projectRoot():
    """
    Root folder of synbio project.
    
    Returns:
        str: absolute path of the root of current project;
             i.e. '/home/raik/py/synbiolib/py/'
    """
    ## import this module
    from evoware import fileutil
    ## get location of this module
    f = absfile(fileutil.__file__)
    ## extract path and assume it is 'project_root/synbio'
    f = osp.join( osp.split( f )[0], '..' )
    return absfile( f )


def testRoot( subfolder='' ):
    """
    Root folder of synbio testdata.
    This method assumes that the python module is located within
    synbiolib/py/.
    
    Args:
        subfolder (str): sub-folder or file within testroot
    
    Returns: 
        str: folder containing testdata
    """
    return absfile( osp.join( projectRoot(), 'evoware', 'testdata', subfolder ) )


def stripFilename( filename ):
    """
    Return filename without path and without ending.

    Args:
        filename (str): name of file
    
    Returns:
        str: base filename
    """
    name = osp.basename( filename )      # remove path
    try:
        if name.find('.') != -1:
            name = name[: name.rfind('.') ]     # remove ending
    except:
        pass  ## just in case there is no ending to start with...

    return name

def tryRemove(f, verbose=0, tree=0, wildcard=0 ):
    """
    Remove file or folder::
     remove(f [,verbose=0, tree=0]) -- remove if possible, otherwise do nothing

    Args:
        f (str): file path
        verbose (bool): report failure (default 0)
        tree (bool): remove whole folder (default 0)
        wildcard (bool): filename contains wildcards (default 0)

    Returns:
       bool: True if file was removed, else False
    """
    try:
        f = absfile( f )
        if osp.isdir(f):
            if tree:
                shutil.rmtree( f, ignore_errors=1 )
            else:
                logging.error('%r is directory - not removed.' % f)
                return False
        else:
            if wildcard:
                l = glob.glob( f )
                for i in l:
                    os.remove( i )
            else:
                os.remove( f )
        return True
    except Exception as why:
        if verbose: logging.warning( 'Cannot remove %r:\n%s' % (f, 
                                                    util.lastError()) )
        return False


######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test MyModule"""

    TAGS = [ testing.NORMAL ]

    def prepare( self ):
        self.fname1 = '~/nonexistent/../subfolder/file.txt'

    def test_stripFilename( self ):
        """fileutil.stripFilename test"""
        r = stripFilename( self.fname1 )
        self.assertEqual( r, 'file', '%r != %r' % (r, 'file') )

    def test_absfilename( self ):
        """fileutil.absfilename test"""
        r = absfile( self.fname1 )
        self.assertEqual( r,
                          osp.join( osp.expanduser('~'), 'subfolder','file.txt'))
        

if __name__ == '__main__':

    testing.localTest()

