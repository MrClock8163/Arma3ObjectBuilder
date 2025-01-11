class ValidatorResult():
    def __init__(self, is_valid = True, comment = ""):
        self.is_valid = is_valid
        self.comment = comment
    
    def __bool__(self):
        return self.is_valid
    
    def set(self, is_valid = True, comment = ""):
        self.is_valid = is_valid
        self.comment = comment


class ValidatorComponent():
    """Base component"""

    @staticmethod
    def is_ascii_internal(value):
        try:
            value.encode("ascii")
            return True
        except:
            return False

    def conditions(self):
        strict = optional = info = ()

        return strict, optional, info
    
    def validate_lazy(self, warns_errs):
        strict, optional, _ = self.conditions()

        for item in strict:
            result = item()
            if not result:
                return False
        
        if warns_errs:
            for item in optional:
                result = item()
                if not result:
                    return False
        
        return True

    def validate_verbose(self, warns_errs):
        strict, optional, info = self.conditions()
        is_valid = True

        for item in strict:
            result = item()
            if not result:
                self.logger.step("ERROR: %s" % result.comment)
                is_valid = False
        
        for item in optional:
            result = item()
            if not result:
                self.logger.step("WARNING: %s" % result.comment)
                is_valid &= not warns_errs
        
        for item in info:
            result = item()
            self.logger.step("INFO: %s" % result.comment)

        return is_valid

    
    def validate(self, lazy, warns_errs):
        is_valid = True

        if lazy:
            is_valid = self.validate_lazy(warns_errs)
        else:
            self.logger.start_subproc("RULESET: %s" % self.__doc__)
            is_valid = self.validate_verbose(warns_errs)
            self.logger.end_subproc()

        return is_valid


class Validator():
    def __init__(self, logger):
        self.logger = logger
    
    def validate(self, *args):
        raise NotImplementedError()
