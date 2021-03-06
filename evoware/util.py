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

"""General purpose utility methods"""

import sys
from inspect import getframeinfo

class ParsingError(Exception):
    pass

def tolist(x):
    """convert input to list if it is not already a list or tuple"""
    if type(x) in [list,tuple]:
        return x
    return [x]


def intfloat2int(x):
    """convert floats like 1.0, 100.0, etc. to int, if possible"""
    if type(x) is float and x % 1 == 0:
        return int(x)
    return x

def lastError():
    """
    Collect type and line of last exception.
    
    Returns:
        str: '<ExceptionType> in line <lineNumber>:<Exception arguments>'
    """
    try:
        trace = sys.exc_info()[2]
        why = sys.exc_info()[1]
        try:
            why = sys.exc_info()[1].args
        except:
            pass
        file = getframeinfo( trace.tb_frame )[0]

        result = "%s in %s line %i:\n\t%s." % ( str(sys.exc_info()[0]),
                  file, trace.tb_lineno, str(why) )

    finally:
        trace = None

    return result

def scriptusage(options:dict={}, doc:str='', minargs:int=1, exit:bool=True, 
                force:bool=False):
    """
    Print a usage help screen to standard out and exit unless there are
    enough command line arguments given. This method only makes sense when
    run from the __main__ context of a python script.
    
    Args:
        options (dict): default options to be listed in usage text
        doc (str): multi-line usage text to print as a help screen
        minargs (int): minimum number of command line arguments to expect 
           (without counting the script name itself);
        exit (bool): exit script after printing help screen
        force (bool): print help and exit no matter what commandline looks like
    """
    
    if len(sys.argv) > minargs and not force:
        return
    
    print(doc)
    
    if len(options) > 1:
        print('Currently defined options:\n')
        for key, value in options.items():
            print("\t-",key, "\t",value)

    if exit: 
        sys.exit(0)


def file2dic( filename ):
    """
    Construct dictionary from file with key - value pairs (one per line).

    Args:
        filename (str): name of file
    
    Raises:
        ParsingError: if file can't be parsed into dictionary
        IOError: if file can't be opened
    """
    try:
        line = None
        result = {}
        for line in open( filename ):

            if '#' in line:
                line = line[ : line.index('#') ]
            line = line.strip()

            l = line.split()[1:]

            if len( l ) == 0 and len( line ) > 0:
                result[ line.split()[0] ] = ''
            if len( l ) == 1:
                result[ line.split()[0] ] = l[0]
            if len( l ) > 1:
                result[ line.split()[0] ] = l
    except IOError:
        raise
    except:
        s = "Error parsing option file %s." % filename
        s += '\nLine: ' + str( line )
        s += '\n' + lastError()
        raise ParsingError( s )

    return result


def get_cmdDict(lst_cmd, dic_default):
    """
    Parse commandline options into dictionary of type ``{<option> : <value>}``
    Options are recognised by a leading '-'.
    Error handling should be improved.
    
    Option " -x <file_name> " is interpreted as file with additional options.
    The key value pairs in lst_cmd replace key value pairs in the
    -x file and in dic_default.
    
    Args:
        lst_cmd (list of str): list with the command line options;
            e.g. ['-pdb', 'in1.pdb', 'in2.pdb', '-o', 'out.dat']
        dic_default (dict of str vs str): dictionary with default options;
            e.g. {'psf':'input.psf'}

    Returns:
        dict: command dictionary; e.g.
             {'pdb':['in1.pdb', 'in2.pdb'], 'psf':'input.psf', 'o':'out.dat'}
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

    except (KeyError, UnboundLocalError) as why:
        raise KeyError("Can't resolve command line options.\n \tError:"+\
              str(why))

    ## get extra options from external file
    try:
        if 'x' in dic_cmd:
            d = file2dic( dic_cmd['x'] )
            d.update( dic_cmd )
            dic_cmd = d
    except IOError:
        raise IOError("Error opening %s."% dic_cmd['x'])

    ## fill in missing default values
    dic_default.update( dic_cmd )
    dic_cmd = dic_default

    return dic_cmd


def cmdDict( defaultDic={} ):
    """
    Convenience implementation of `get_cmdDict`. Take command line options
    from sys.argv[1:] and convert them into dictionary.

    Example:
      '-o out.dat -in 1.pdb 2.pdb 3.pdb -d' will be converted to
      {'o':'out.dat', 'in': ['1.pdb', '2.pdb', '3.pdb'], 'd':'' }
      
    Option " -x <file_name> " is interpreted as file with additional options.
    
    Args:
        defaultDic (dict): dic with default values.

    Returns:
        dict: command dictionary
    """
    return get_cmdDict( sys.argv[1:], defaultDic )

