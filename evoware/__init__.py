##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2016 Raik Gruenberg, All Rights Reserved
VERSION = (0,1,5)

__version__ = '.'.join([ str(i) for i in VERSION])
__VERSION__ = __version__

## add evowarepy/thirdparty to PYTHONPATH so that third party python modules
## can be bundled directly with the source code
import os.path as osp
import sys

project_root = osp.abspath( osp.split( osp.abspath(__file__) )[0] )

sys.path.append( osp.join( project_root, 'thirdparty'))

## Import main classes into package name space for convenience
from evoware.evotask import EvoTask
from evoware.worklist import Worklist, WorklistException
from evoware.plates import PlateFormat, PlateError, Plate
from evoware.plateindex import PlateIndex, PlateIndexError
plates = PlateIndex()

from evoware.cherrypicking import SourceIndex, TargetIndex, CherryWorklist, IndexFileError

## documentation hints:
## * napoleon sphinx extension for readable docstrings: 
##   http://www.sphinx-doc.org/en/stable/ext/napoleon.html
## * .. default-role:: any
##   activates much more convenient ref / linking to methods and classes

