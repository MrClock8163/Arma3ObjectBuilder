import os
import re


class RVMATTemplateField:
    def __init__(self, string):
        if not string.startswith("<") or not string.endswith(">") or string.count("|") != 2:
            print(string)
            raise ValueError("Invalid RVMAT template field definition")
        
        string = string[1:-1]
        suffixes, extensions, default = string.split("|")

        self.suffixes = [("_%s" % item.strip().lower()) for item in suffixes.split(",")]
        self.extensions = [(".%s" % item.strip().lower()) for item in extensions.split(",")]

        self.default = default
    
    def generate_paths(self, folder, basename):
        return [os.path.join(folder, basename + sfx + ext) for sfx in self.suffixes for ext in self.extensions]
    
    def generate_value(self, root, folder, basename, check_files_exist):
        paths = self.generate_paths(folder, basename)
        print(paths)

        for item in paths:
            if os.path.isfile(item):
                return os.path.relpath(item, root)
        
        if not check_files_exist:
            return os.path.relpath(paths[0], root)
        
        return self.default


class RVMATTemplate:
    RE_STAGE = re.compile(r"<.*>")

    def __init__(self, filepath):
        self.fields = []
        with open(filepath) as file:
            self.template = file.read()

        for match in self.RE_STAGE.finditer(self.template):
            try:
                self.fields.append(RVMATTemplateField(match.group(0)))
            except ValueError as ex:
                self.fields.append(None)
    
    def write_output(self, root, folder, basename, check_files_exist):
        values = ((field.generate_value(root, folder, basename, check_files_exist) if field else None) for field in self.fields)
        
        def repl(match):
            string = next(values)
            if string is None:
                return match.group(0)
            
            return "\"%s\"" % string
        
        try:
            if not os.path.isdir(folder):
                os.makedirs(folder)

            with open(os.path.join(folder, basename + ".rvmat"), "w") as file:
                file.write(self.RE_STAGE.sub(repl, self.template))
                return True
            
        except Exception as ex:
            print(ex)
            return False
