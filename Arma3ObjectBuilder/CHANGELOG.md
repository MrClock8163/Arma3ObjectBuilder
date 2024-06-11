# Changelog

## [v2.3.4](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.3.4) (Blender 2.90 -> 4.2)

### Added

- extension manifest `blender_manifest.toml`

### Changed

- updated internal references for compatibility with **Blender 4.2**+

## [v2.3.3](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.3.3) (Blender 2.90 -> 4.1)

### Fixed

- Extract Proxy would fail due to missing internal property

## [v2.3.2](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.3.2) (Blender 2.90 -> 4.1)

### Added

- import-export:
  - ASC import drag-and-drop support (Blender 4.1 and above)
  - P3D import drag-and-drop support (Blender 4.1 and above)
  - RTM import drag-and-drop support (Blender 4.1 and above)
  - Skeleton import drag-and-drop support (Blender 4.1 and above)

## [v2.3.1](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.3.1) (Blender 2.90 -> 4.1)

### Fixed

- Sort Sections P3D export option was operating on the wrong object, and wasn't actually affecting the output model

## [v2.3.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.3.0) (Blender 2.90 -> 4.1)

### Added

- Materials tool RVMAT Templates
- import-export:
  - P3D:
    - support for Underground (VBS) LOD type
    - support for Groundlayer (VBS) LOD type
    - support for Navigation (VBS) LOD type
    - Collisions export option (handling duplicate LOD types)
    - Generate Components export option
    - LOD copy directives
- Validation tool:
  - LOD - Generic ruleset:
    - warning for more than 2 UV channels on a LOD object
  - LOD - Shadow ruleset:
    - warning for unconventinal LOD indices (not 0, 10, 1000, 1010 or 1020)
    - warning if LOD has `lodnoshadow = 1` named property
  - LOD - Underground (VBS) ruleset
  - LOD - Groundlayer (VBS) ruleset
- Rigging tool:
  - Add OFP2_ManSkeleton operator
- Debug add-on options tab:
  - Preserve Preprocessed LOD Objects

### Changed

- import-export:
  - export processes will no longer start if the target file is in use by another application
  - backup and temporary export files are now time stamped in the extension to avoid collisions
  - P3D:
    - handling of unknown LOD types has been improved (the Unknown LOD type can now be used to set any custom LOD signature)
- utilities:
  - Find Components now only creates selections for closed components
- Vertex Mass Editing tool:
  - Mass From Density now ignores non-closed components and loose vertices
- Rigging tool:
  - skeletons and bones are no longer forcibly alphabetically sorted
  - hierarchic bone order now has to be maintained manually, depending processed will not try to detect the hierarchy in a mixed order
- Colors tool was moved under new Materials tool
- Preserve Faulty Output add-on option was moved to the newly introduced Debug options tab

### Fixed

- Geometry LOD validation would falsely report not triangulated meshes
- P3D import would crash Blender if Proxy Action was set to Purge
- Find Components would purge all vertex groups under certain circumstances

## [v2.2.1](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.2.1) (Blender 2.90 -> 4.1)

### Added

- Center Of Mass operator in the Vertex Mass Editing tool (forgot to include in v2.2.0)

### Changed

- Arma 3 Proxy object can now be added to the scene without first selecting a parent object

### Fixed

- P3D import and export would fail in older versions of Blender when trying to remove unnecessary UV layers from objects
- geometry node modifiers would not be applied during P3D export
- length limit on P3D named property names and values was missing and would result in a failed export at too long values

## [v2.2.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.2.0) (Blender 2.90 -> 4.1)

### Added

- common data:
  - support for penetration materials
- tools:
  - Rigging:
    - Validate (skeleton)
    - Validate For RTM (skeleton)
- import-export:
  - P3D:
    - Translate Selections import option
    - Cleanup Selections import option
    - Preserve/Merge sections import option
  - RTM:
    - support for importing binarized (BMTR) animations
- scripts:
  - script to convert binarized (BMTR) animations to plain RTM representation

### Changed

- Blender 4.1 compatiblity:
  - updated P3D import and export to be compatible with the new Blender API
  - updated Validation tool to be compatible with the new Blender API
- common data:
  - common items are now displayed in alphabetical order by default
- tools:
  - Validation:
    - validation now checks for non-ASCII characters in named properties, paths and vertex group names
    - internal logic is now standardized
- import-export:
  - read strings are now decoded as UTF-8 in order to improve robustness
  - P3D:
    - new proxy triangles (imported or created) are now displayed as wireframes, and show their object names
    - UV channels are now only exported for visual and shadow LODs
  - RTM:
    - simplified internal handling of the RTM matrix data
    - default import frame mapping method is now "Direct"

### Fixed

- Vertex Mass Editing tool would potentially throw silent errors in certain conditions
- material properties panel would throw silent errors in certain conditions
- remove RTM frame operator would throw silent errors and would not work properly
- Extract Proxy operator would fail due to missing properties
- P3D import would fail at proxy separation if the materials are not allowed as additional data
- P3D export would fail at applying transformations if a LOD object was in edit mode when starting the export (rare edge case)

### Removed

- Check Hierarchy operator was removed from the Rigging tool (replaced by the Validate, and Validate For RTM operators)

## [v2.1.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.1.0) (Blender 2.90 -> 4.0)

### Added

- tools:
  - Validation:
    - Point cloud ruleset
    - Paths ruleset
    - Roadway ruleset
  - Rigging:
    - new tool panel consolidating rigging related tools
    - Add/Remove Skeleton definitions
    - Add/Remove Bone to/from Skeleton definition
    - Skeleton From Armature
    - Pivots From Armature
- properties:
  - Proxy Access sub-panel in LOD Properties
    - direct access to proxy properties
    - Add Proxy
    - Remove Proxy
- import-export:
  - new options in RTM export (sampling options)
  - new options in ASC import and export
  - new Absolute Paths option in P3D import
  - new Relative Paths option in P3D export
  - RTM import
  - Skeleton import (from model.cfg)
  - Armature import (from pivots.p3d and selected skeleton definition)
- template scripts (Text editor Templates menu)
- Create Backups add-on option

### Changed

- tools:
  - Validation logic was completely overhauled for better extensibility
  - Weight Painting tool was reworked and moved under the new Rigging tool panel
  - Utility functions in the Vertex Groups panel were moved to a menu
- import-export:
  - P3D:
    - split normals are now only imported for visual LODs
    - split normals are now only exported for visual LODs
    - when custom normals are not exported, they are now replaced with weighted normals automatically
    - shadow LODs are now imported as flat shaded
  - RTM:
    - export now requires a skeleton definition to filter out control bones of IK rigs
- properties:
  - RTM properties were moved from the armature, to the active animation action
  - DTM:
    - properties panel was renamed to DTM Properties
    - Raster Spacing property was renamed to Cell Size
    - Reference Point property was changed to Data Type

### Fixed

- LOD validation would produce false negatives when proxies were used
- LOD type would be detected incorrectly for Shadow Volume - View Cargo when the resolution is higher than 4
- LOD resolution would be incorrectly exported for Shadow Volume - View Cargo
- fixed possible issue in P3D export when the material index of a face is out of the material range for some reason
- add-on installation would fail on non-windows systems
- ASC import would delete source file if an error occured during importing
- User value would not be displayed correctly in the default Face Flag editing options

### Removed

- Conversion tool was removed (conversion was made available as a ready-to-run template script instead)
- RTM Frames tool was removed
- RTM Properties panel was removed from Armature objects
- Export Relative add-on option (option is now integrated into the P3D export options)
- Reconstruct Absolute Paths add-on option (option is now integrated into the P3D import options)

## [v2.0.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v2.0.0) (Blender 2.90 -> 4.0)

**This update brings compatibility with the Blender 4 releases**

### Added

- preferences:
  - Defaults tab for default fallback values
  - option to enable-disable the Outliner tool
- tools:
  - Outliner
- object properties:
  - Vertex Flag Groups
  - Face Flag Groups
- new operators:
  - Copy Proxy
  - Copy Proxies
  - Transfer Proxies
  - Paste Common Material
  - Paste Common Procedural
- common items:
  - 4 new proxy paths included
  - support for material paths
  - support for procedural texture strings
- import-export:
  - option to force lower case bone names during RTM export
  - option to force lower case file paths and selection names during P3D export
  - option to renumber components during P3D export

### Changed

- preferences:
  - Arma 3 Tools path was moved to the path settings category
- Blender 4 compatibility:
  - updated internal operator calls to be compatible with the new Blender API
  - updated Live Mass Editing to be compatible with the new Blender API
- named properties:
  - operators now correctly operate on the object displayed in the properties tab, instead of the active view-layer object
  - names and values are now editable in the list directly
- import-export:
  - P3D import-export complete overhaul
    - file is now first read completely and kept in memory during the import process
    - import speed increase
    - updated import-export logging
    - edges of flat shaded faces are now only exported as sharp, if the entire LOD is flat shaded
    - mesh validation is no longer default during P3D import or export
  - RTM export complete overhaul
- tools:
  - Validation now correctly considers modifiers
  - Vertex Mass Editing now operates on the context object (object shown in the properties panel) instead of the active object

### Fixed

- RTM export would not delete faulty outputs and raise an exception due to a missing module import
- P3D import would sometimes fail due to mismatching normals-loops count (on topoologically defective models)
- ASCIIZ strings and characters were mistakenly decoded as UTF-8 (with no practical consequence)
- P3D output would become potentially faulty if non-manifold edges were marked as sharp

### Removed

- Dynamic Object Naming (from LOD objects)
- Vertex Normals Flag LOD object property (use the new Vertex Flag Groups instead)

## [v1.0.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v1.0.0) (Blender 2.90 -> 3.6)

### Added

- Move Bottom utility function
- Sort Sections option in P3D export
- custom UI icons (for dark and light UI themes)
- Find Arma 3 Tools function in add-on preferences
- Analyze sub-panel with mass distribution visualization function in Vertex Mass Editing tool panel

### Changed

- Sort function was renamed to Move Top
- help links are now displayed on property panels as well
- P3D export now only processes visible LOD objects
- multiple functions were updated to not split-merge the meshes and use internal functions instead (eg.: Find Components, Mass From Density etc.)
- Redefine Vertex Group now modifies the existing group instead of removing and recreating it
- Vertex Mass Editing panel items are now always visible
- tool panel properties are now saved in blend files and are persistent across sessions

### Fixed

- P3D export would fail if a LOD object was in edit mode
- P3D export would fail if a LOD object had a non-mesh child object
- setup conversion would fail with materials using procedural colors
- proxy tools panel would throw exception if no object was active in the scene
- documentation link would not show up in add-on preferences in newer Blender versions
- Component Convex Hull would not actually perform convex hull on all components

### Removed

- Translucent option in material properties

## [v0.3.4](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.3.4) (Blender 2.90 -> 3.6)

### Added

- support for relative paths (not recommended to be used though)
- option to only import 1st P3D LOD
- option to validate P3D LODs during export

### Changed

- files during exports are now first written to *.temp files which are cleaned up in case an error occurs
- validation can now be run on all LOD types
- the UVSet0 embedded into the geometry data is no longer discarded during P3D import
- reduced the number of vertex normals written to P3D files by eliminating duplicates

### Fixed

- fixed an error in the P3D import where random sharp edges would appear on the model under certain conditions
- fixed various back-end issues with edge cases

## [v0.3.3](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.3.3) (Blender 2.90 -> 3.6)

### Added

- new utility functions:
  - Sort faces
  - Recalculate Normals
- Color converter tool
- Weight Painting cleanup tools
- Fixed Vertex Normals option to LOD properties

### Changed

- file names of UI implementations now represent their context
- exception logging during I/O operations was made cleaner
- documentation links now point to the new GitBook

### Fixed

- exception would occur in newer Blender versions during vertex mass editing (due to a so-far-unnoticed API difference in the bmesh module)

## [v0.3.2](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.3.2) (Blender 2.90 -> 3.6)

### Added

- Align With Object proxy operator
- Dynamic Object Naming for LOD and proxy objects
- Addon Preference option to show/hide tool help links
- Renaming tools
  - Bulk Rename
  - Root Rename
  - Vertex Groups
- Calculated raster spacing for raster DTMs

### Changed

- renamed Align Coordinate System operator to Realign Coordinate System

### Fixed

- proxy transformation issue during import

## [v0.3.1](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.3.1) (Blender 2.90 -> 3.6)

### Added

- Proxies tool panel
- Extract Proxy functionality
- Align Coordinate System functionality

### Changed

- all tool panels are now collapsed by default
- Vertex Mass Editing panel is now visible in Object Mode too
- LODs are now sorted by their resolution signatures before export

### Fixed

- the P3D import would fail if there was an object already selected in the scene
- the magazine proxy path in the common proxies list had a typo

## [v0.3.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.3.0) (Blender 2.90 -> 3.6)

### Added

- Export - Arma 3 animation (*.rtm)
- RTM Frames tool
- RTM properties
- Setup conversion - DTM
- Setup conversion - Armature

## [v0.2.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.2.0) (Blender 2.90 -> 3.6)

### Added

- Import - Esri ASCII grid (*.asc)
- Export - Esri ASCII grid (*.asc)

## [v0.1.0](https://github.com/MrClock8163/Arma3ObjectBuilder/releases/tag/v0.1.0) (Blender 2.90 -> 3.6)

Initial release

### Added

- P3D import (MLOD)
- P3D export (MLOD)
- interfaces to edit all P3D properties
- conversion from ArmaToolbox-style setup
- LOD mesh validation
- hit point cloud generation
