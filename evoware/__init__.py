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

VERSION = (0,1,6)

__version__ = __VERSION__ = '.'.join([ str(i) for i in VERSION])

## add evowarepy/thirdparty to PYTHONPATH so that third party python modules
## can be bundled directly with the source code
import os.path as osp
import sys

project_root = osp.abspath( osp.split( osp.abspath(__file__) )[0] )

sys.path.append( osp.join( project_root, 'thirdparty'))


## documentation hints:
## * napoleon sphinx extension for readable docstrings: 
##   http://www.sphinx-doc.org/en/stable/ext/napoleon.html
## * .. default-role:: any
##   activates much more convenient ref / linking to methods and classes

