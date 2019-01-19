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

"""General purpose methods; mostly about file handling"""

import os.path as osp
import os
import shutil, glob, sys

import logging

import util

class UtilError( Exception ):
    pass


def absfile( filename, resolveLinks=1 ):
    """
    Get absolute file path::
      - expand ~ to user home, change
      - expand ../../ to absolute path
      - resolve links
      - add working directory to unbound files ('ab.txt'->'/home/raik/ab.txt')

    @param filename: name of file
    @type  filename: str
    @param resolveLinks: eliminate any symbolic links (default: 1)
    @type  resolveLinks: 1|0
    
    @return: absolute path or filename
    @rtype: string

    @raise ToolsError: if a ~user part does not translate to an existing path
    """
    if not filename:
        return filename
    r = osp.abspath( osp.expanduser( filename ) )

    if '~' in r:
        raise UtilError, 'Could not expand user home in %s' % filename

    if resolveLinks:
        r = osp.realpath( r )
    r = osp.normpath(r)
    return r


def projectRoot():
    """
    Root folder of synbio project.
    
    @return: absolute path of the root of current project::
             i.e. '/home/raik/py/synbiolib/py/'
    @rtype: string
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
    @param subfolder: str; sub-folder within testroot
    @return: str; folder containing testdata
    """
    return absfile( osp.join( projectRoot(), 'evoware', 'testdata', subfolder ) )


def stripFilename( filename ):
    """
    Return filename without path and without ending.

    @param filename: name of file
    @type  filename: str
    
    @return: base filename
    @rtype: str
    """
    name = osp.basename( filename )      # remove path
    try:
        if name.find('.') <> -1:
            name = name[: name.rfind('.') ]     # remove ending
    except:
        pass  ## just in case there is no ending to start with...

    return name

def tryRemove(f, verbose=0, tree=0, wildcard=0 ):
    """
    Remove file or folder::
     remove(f [,verbose=0, tree=0]), remove if possible, otherwise do nothing

    @param f: file path
    @type  f: str
    @param verbose: report failure (default 0)
    @type  verbose: 0|1
    @param tree: remove whole folder (default 0)
    @type  tree: 0|1
    @param wildcard: filename contains wildcards (default 0)
    @type  wildcard: 0|1

    @return: 1 if file was removed
    @rtype: 1|0
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
    except Exception, why:
        if verbose: logging.warning( 'Cannot remove %r:\n%s' % (f, 
                                                    util.lastError()) )
        return False

## quick and dirty command line argument parsing... could be made more elegant
def get_cmdDict(lst_cmd, dic_default):
    """
    Parse commandline options into dictionary of type C{ {<option> : <value>} }
    Options are recognised by a leading '-'.
    Error handling should be improved.
    
    Option C{ -x |file_name| } is interpreted as file with additional options.
    The key value pairs in lst_cmd replace key value pairs in the
    -x file and in dic_default.
    

    @param lst_cmd: list with the command line options::
                    e.g. ['-pdb', 'in1.pdb', 'in2.pdb', '-o', 'out.dat']
    @type  lst_cmd: [str]
    @param dic_default: dictionary with default options::
                        e.g. {'psf':'in.psf'}
    @type  dic_default: {str : str}

    @return: command dictionary::
             ala {'pdb':['in1.pdb', 'in2.pdb'], 'psf':'in.psf', 'o':'out.dat'}
    @rtype: {<option> : <value>}
    """
    dic_cmd = {}                     # create return dictionary
    try:

        for cmd in lst_cmd:
            if (cmd[0] == '-'):               # this entry is new option
                current_option = cmd[1:]      # take all but leading "-"
                dic_cmd[current_option] = ""  # make sure key exists even
                                              # w/o value
                counter = 0        # number of values for this option
            else:                  # this entry is value for latest option

                if counter < 1:
                    dic_cmd[current_option] = cmd

    # in case, several values follow after a "-xxx" option convert dictionary
    # entry into list and add all elements (until the next "-") to this list
                else:
                    if counter == 1:   # there is already a value assigned
    # convert to list
                        dic_cmd[current_option] = [dic_cmd[current_option]]
    # add value to list
                    dic_cmd[current_option] = dic_cmd[current_option] + [cmd]

                counter = counter + 1

    except (KeyError, UnboundLocalError), why:
        raise UtilError, "Can't resolve command line options.\n \tError:"+\
                  str(why)

    ## get extra options from external file
    try:
        if dic_cmd.has_key('x'):
            d = file2dic( dic_cmd['x'] )
            d.update( dic_cmd )
            dic_cmd = d
    except IOError:
        raise IOError, "Error opening %s."% dic_cmd['x']

    ## fill in missing default values
    dic_default.update( dic_cmd )
    dic_cmd = dic_default

    return dic_cmd


def cmdDict( defaultDic={} ):
    """
    Convenience implementation of L{get_cmdDict}. Take command line options
    from sys.argv[1:] and convert them into dictionary.
    Example::
      '-o out.dat -in 1.pdb 2.pdb 3.pdb -d' will be converted to
      {'o':'out.dat', 'in': ['1.pdb', '2.pdb', '3.pdb'], 'd':'' }
      
    Option C{ -x |file_name| } is interpreted as file with additional options.
    
    @param defaultDic: dic with default values.
    @type  defaultDic: dic

    @return: command dictionary
    @rtype: dic
    """
    return get_cmdDict( sys.argv[1:], defaultDic )


######################
### Module testing ###
import testing

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
                          osp.join( osp.expanduser('~'), 'subfolder/file.txt'))
        

if __name__ == '__main__':

    testing.localTest()

