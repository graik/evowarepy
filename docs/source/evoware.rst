API Documentation
=================

Sample handling
---------------

Classes for handling and identifying samples and plates or labware.

.. currentmodule:: evoware

.. autosummary::
   :nosignatures:
   :toctree: evoware
   :template: autosummary/class_details.rst
   
   Sample
   TargetSample
   SampleList
   PlateFormat
   Plate
   PlateIndex
   plates


Evoware Worklists
------------------

The following classes support the generation of 
Tecan "work lists", that is, custom-formatted textfiles with
instructions for the robot. 

.. autosummary::
   :nosignatures:
   :toctree: evoware
   :template: autosummary/class_details.rst

   Worklist
   SampleWorklist
   
   
Working with Excel files
------------------------

The core Excel parsing is found in the evoware.excel sub-package:

.. toctree::
   :maxdepth: 2

   evoware.excel

Excel files are parsed into dictionaries that are then converted into Sample
information using different converter classes:

.. autosummary::
   :nosignatures:
   :toctree: evoware
   :template: autosummary/class_details.rst
  
   SampleConverter
   PickingConverter
   DistributionConverter

Helper Modules
--------------

Modules with utility and helper methods. 

.. currentmodule:: evoware

.. autosummary::
   :toctree: evoware
   :template: autosummary/module_with_details.rst

   fileutil
   util
   dialogs

Exceptions
----------

The following errors are defined by evoware.

.. autosummary::
   :nosignatures:
   :toctree: evoware
   :template: autosummary/class_details.rst

   SampleError
   SampleValidationError
   PlateError
   PlateIndexError
   WorklistException
