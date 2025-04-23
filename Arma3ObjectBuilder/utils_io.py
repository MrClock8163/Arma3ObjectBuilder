import os
from datetime import datetime

import bpy

from . import get_prefs


def replace_slashes(path):
    return path.replace("/", "\\")


def abspath(path):
    if not path.startswith("//"):
        return path

    return os.path.abspath(bpy.path.abspath(path))


# Attempt to restore absolute paths to the set project root (P drive by default).
def restore_absolute(path, extension = ""):
    path = replace_slashes(path.strip().lower())
    
    if path == "":
        return ""
    
    if os.path.splitext(path)[1].lower() != extension:
        path += extension
    
    root = abspath(get_prefs().project_root).lower()
    if not path.startswith(root):
        abs_path = os.path.join(root, path)
        if os.path.exists(abs_path):
            return abs_path
    
    return path


def make_relative(path, root):
    path = path.lower()
    root = root.lower()
    
    if root != "" and path.startswith(root):
        return os.path.relpath(path, root)
    
    drive = os.path.splitdrive(path)[0]
    if drive:
       path = os.path.relpath(path, drive)
    
    return path


def format_path(path, root = "", to_relative = True, extension = True):
    path = replace_slashes(path.strip())
    
    if to_relative:
        root = replace_slashes(root.strip())
        path = make_relative(path, root)
        
    if not extension:
        path = os.path.splitext(path)[0]
        
    return path


class ExportFileHandler():
    def __init__(self, filepath, mode):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.filepath = filepath
        self.temppath = "%s.%s.temp" % (filepath, timestamp)
        self.mode = mode
        self.file = None
        addon_pref = get_prefs()
        self.backup_old = addon_pref.create_backups
        self.preserve_faulty = addon_pref.preserve_faulty_output

    def __enter__(self):
        file = open(self.temppath, self.mode)
        self.file = file

        return file

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

        if exc_type is None:
            if os.path.isfile(self.filepath) and self.backup_old:
                self.force_rename(self.filepath, self.filepath + ".bak")

            self.force_rename(self.temppath, self.filepath)
        
        elif not self.preserve_faulty:
            os.remove(self.temppath)
    
    @staticmethod
    def force_rename(old, new):
        if os.path.isfile(new):
            os.remove(new)
        
        os.rename(old, new)
