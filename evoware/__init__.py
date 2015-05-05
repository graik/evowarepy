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

VERSION = (0,1,3)

__version__ = '.'.join([ str(i) for i in VERSION])
__VERSION__ = __version__

## add evowarepy/thirdparty to PYTHONPATH so that third party python modules
## can be bundled directly with the source code
import os.path as osp
import sys

project_root = osp.abspath( osp.split( osp.abspath(__file__) )[0] )

sys.path.append( osp.join( project_root, 'thirdparty'))

## Import main classes into package name space for convenience
from evotask import EvoTask
from worklist import Worklist, WorklistException
from plates import PlateFormat, PlateError
from cherrypicking import SourceIndex, TargetIndex, CherryWorklist, IndexFileError

