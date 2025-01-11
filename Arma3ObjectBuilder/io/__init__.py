if "binary_handler" in locals():
    from importlib import reload
    
    if "binary_handler" in locals():
        reload(binary_handler)
    if "compression" in locals():
        reload(compression)
    if "data_p3d" in locals():
        reload(data_p3d)
    if "export_p3d" in locals():
        reload(export_p3d)
    if "import_p3d" in locals():
        reload(import_p3d)


from . import binary_handler
from . import compression
from . import data_p3d
from . import export_p3d
from . import import_p3d
