from typing import Any, TypeAlias
from collections.abc import Callable

from .logger import ProcessLogger


class ValidatorResult():
    def __init__(self, is_valid: bool = True, comment: str = "") -> None:
        self.is_valid: bool = is_valid
        self.comment: str = comment

    def __bool__(self) -> bool:
        return self.is_valid

    def set(self, is_valid: bool = True, comment: str = "") -> None:
        self.is_valid = is_valid
        self.comment = comment


ValidatorFunctionType: TypeAlias = Callable[[], ValidatorResult]


class ValidatorComponent():
    """Base component"""

    def __init__(self, logger: ProcessLogger) -> None:
        self.logger: ProcessLogger = logger

    @staticmethod
    def is_ascii_internal(value: str) -> bool:
        try:
            value.encode("ascii")
            return True
        except Exception:
            return False

    def conditions(self) -> tuple[
        tuple[ValidatorFunctionType, ...],
        tuple[ValidatorFunctionType, ...],
        tuple[ValidatorFunctionType, ...]
    ]:
        strict = optional = info = ()

        return strict, optional, info

    def validate_lazy(self, warns_errs: bool) -> bool:
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

    def validate_verbose(self, warns_errs: bool) -> bool:
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

    def validate(self, lazy: bool, warns_errs: bool) -> bool:
        is_valid = True

        if lazy:
            is_valid = self.validate_lazy(warns_errs)
        else:
            self.logger.start_subproc("RULESET: %s" % self.__doc__)
            is_valid = self.validate_verbose(warns_errs)
            self.logger.end_subproc()

        return is_valid


class Validator():
    def __init__(self, logger: ProcessLogger) -> None:
        self.logger: ProcessLogger = logger

    def validate(self, *args: Any) -> bool:
        raise NotImplementedError()
