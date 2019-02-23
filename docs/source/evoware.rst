API Documentation
=================

Sample & Plate handling
-----------------------

Plates define labware instances such as tube racks or microwell plates.  
The relevant classes are defined in `evoware.plates`. A singleton (static)
`index` variable holds a package-wide registry of currently known 
plate instances.

.. currentmodule:: evoware.plates

.. autosummary::
   :nosignatures:
   :toctree: evoware
   :template: autosummary/class_details.rst

   PlateFormat
   Plate
   PlateIndex
   index


Samples define single wells or tubes within plates. A `Reaction` is a special
kind of sample that tracks how much volume it is supposed to receive from other
(source) `Sample`s. The relevant classes are found in the `evoware.samples`
module.

.. currentmodule:: evoware.samples

.. autosummary::
   :nosignatures:
   :toctree: evoware
   :template: autosummary/class_details.rst
   
   Sample
   Reaction
   SampleList
   SampleIndex


Tecan Worklists
------------------

The following classes support the generation of 
Tecan "work lists", that is, custom-formatted textfiles with
instructions for the robot. 

.. currentmodule:: evoware.tecan
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

