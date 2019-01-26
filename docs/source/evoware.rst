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
   

