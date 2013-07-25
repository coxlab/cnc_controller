cnc_controller
==============

A controller... for the CNC!


Structure
==============

The general application structure is a (very leaky) view-controller where the view (gui) is 
written in pyObjC and the controller:

- manager coordinate frame transformations [skull -> tricorner hat, tricorner hat -> camera, etc...]
- talks to the stereo cameras
- talks to the cnc
- talks to mworks (this is actually done in the gui and is one of the 'leaks')


Controller
==============

see electrodeController and ocController.py

Contains:

- camera lens calibrations (calibrations)
- camera io & stereo code (camera)
- config files for camera, atlas, cnc, coordinate frames, etc... (cfg)
- cnc io & line/path fitting (cnc)
- frame manager for transforming coordinates across frames (frameManager.py)
- obj [3d mesh] loading code (objLoader.py)
- main/core class (controller.py)


View
==============
some in ocController.py

- atlas : ocAtlasView.py
- 3d mesh view : ocMeshView.py
- camera view : ocZoomView.py
