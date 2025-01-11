if "binary_handler" in locals():
    from importlib import reload
    
    if "binary_handler" in locals():
        reload(binary_handler)
    if "compression" in locals():
        reload(compression)
    if "data_asc" in locals():
        reload(data_asc)
    if "data_p3d" in locals():
        reload(data_p3d)
    if "data_rtm" in locals():
        reload(data_rtm)
    if "data_tbcsv" in locals():
        reload(data_tbcsv)
    if "export_asc" in locals():
        reload(export_asc)
    if "export_p3d" in locals():
        reload(export_p3d)
    if "export_rtm" in locals():
        reload(export_rtm)
    if "export_tbcsv" in locals():
        reload(export_tbcsv)
    if "import_armature" in locals():
        reload(import_armature)
    if "import_asc" in locals():
        reload(import_asc)
    if "import_p3d" in locals():
        reload(import_p3d)
    if "import_rtm" in locals():
        reload(import_rtm)
    if "import_tbcsv" in locals():
        reload(import_tbcsv)


from . import binary_handler
from . import compression
from . import data_asc
from . import data_p3d
from . import data_rtm
from . import data_tbcsv
from . import export_asc
from . import export_p3d
from . import export_rtm
from . import export_tbcsv
from . import import_armature
from . import import_asc
from . import import_p3d
from . import import_rtm
from . import import_tbcsv
