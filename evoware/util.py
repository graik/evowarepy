##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved
"""General purpose utility methods"""

import sys
from inspect import getframeinfo

class ParsingError(Exception):
    pass

def tolist(x):
    if type(x) in [list,tuple]:
        return x
    return [x]

def lastError():
    """
    Collect type and line of last exception.
    
    @return: '<ExceptionType> in line <lineNumber>:<Exception arguments>'
    @rtype: String
    """
    try:
        trace = sys.exc_info()[2]
        why = sys.exc_info()[1]
        try:
            why = sys.exc_info()[1].args
        except:
            pass
        file = getframeinfo( trace.tb_frame )[0]

        result = "%s in %s line %i:\n\t%s." % ( str(sys.exc_type),
                  file, trace.tb_lineno, str(why) )

    finally:
        trace = None

    return result


def file2dic( filename ):
    """
    Construct dictionary from file with key - value pairs (one per line).

    @param filename: name of file
    @type  filename: str
    
    @raise ParsingError: if file can't be parsed into dictionary
    @raise IOError: if file can't be opened
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
        raise KeyError, "Can't resolve command line options.\n \tError:"+\
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

