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

"""Short one-line description of this module"""

import sys ## keep import statements at the top of the module


class ExampleException( Exception ):
    pass


class ExampleClass( object ):
    """
    Detailed description of this class.

    The first letter of a class is Uppercase. All classes should be
    derived from object to allow the use of properties in Python 2.

    Coding rules:

      * Indentation -- 4 spaces; no Tab characters. Adapt your editor!

      * Reporting -- don't use print statements anywhere within library classes.

      * Width -- please try to keep your code within the classic 80 char. limit.
    """

    def __init__(self, name, parent=None, verbose=0 ):
        """
        Describe all arguments of the method so that they can be parsed by
        epydoc.
        
        @param name:   str; name of this object
        @param parent: ExampleClass; parent object [None]
        @param verbose: int; verbosity level from 0 (default) to 3
        """
        ## try declaring all fields 
        self.name = name
        self._parent = parent
        self.verbose = verbose


    def reportSomething( self ):
        """
        Create a simple report.
        @return: str; Fake report
        """
        return "%s: Hello World!" % self.name

    ## Use properties!
    def setParent( self, o ):
        self._parent = str(o)

    def getParent( self ):
        return self._parent

    parent = property( getParent, setParent )

    ## Override Python special methods!
    def __str__( self ):
        """String representation of this object"""
        if not self.parent:
            return self.name

        return str( self.parent ) + ' > ' + self.name

######################
### Module testing ###
from evoware import testing

class Test(testing.AutoTest):
    """Test GoodCodeTemplate"""

    TAGS = [ testing.LONG ]

    def prepare( self ):
        self.e1 = ExampleClass( 'example1' )

    def test_exampleReport( self ):
        """ExampleClass.report test"""
        self.result = self.e1.reportSomething()

        if self.local:   ## only if the module is executed directly
            print()
            print(self.result) 

        self.assertEqual( self.result, 'example1: Hello World!',
                          'unexpected result' )

    def test_exampleParent( self ):
        """ExampleClass.parent test"""
        self.e2 = ExampleClass( 'example2' )
        self.e2.parent = self.e1
        
        if self.local:
            print()
            print(self.e2)

        self.assertEqual( str(self.e2), 'example1 > example2' )

if __name__ == '__main__':

    testing.localTest()
