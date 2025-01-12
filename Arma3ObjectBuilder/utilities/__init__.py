if "data" in locals():
    from importlib import reload
    
    if "data" in locals():
        reload(data)
    if "clouds" in locals():
        reload(clouds)
    if "colors" in locals():
        reload(colors)
    if "proxy" in locals():
        reload(proxy)
    if "renaming" in locals():
        reload(renaming)
    if "flags" in locals():
        reload(flags)
    if "lod" in locals():
        reload(lod)
    if "masses" in locals():
        reload(masses)
    if "outliner" in locals():
        reload(outliner)
    if "rigging" in locals():
        reload(rigging)
    if "structure" in locals():
        reload(structure)


# In order of dependency
from . import data
from . import clouds
from . import colors
from . import proxy
from . import renaming
from . import flags
from . import lod
from . import masses
from . import outliner
from . import rigging
from . import structure
