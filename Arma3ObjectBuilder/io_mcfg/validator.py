from typing import Any

from ..logger import ProcessLogger
from ..validation import ValidatorResult, ValidatorComponent, Validator, ValidatorFunctionType


class ValidatorComponentSkeleton(ValidatorComponent):
    """Skeleton - Base component"""

    def __init__(
        self,
        skeleton: Any,
        logger: ProcessLogger
    ) -> None:
        self.skeleton: Any = skeleton
        self.logger: ProcessLogger = logger

    def has_valid_name(self) -> ValidatorResult:
        result = ValidatorResult()

        if not self.is_ascii_internal(self.skeleton.name) or " " in self.skeleton.name:
            result.set(False, "skeleton name contains spaces and/or non-ASCII characters")

        return result

    def only_unique_bones(self) -> ValidatorResult:
        result = ValidatorResult()

        names = set()
        for bone in self.skeleton.bones:
            if bone.name.lower() in names:
                result.set(False, "skeleton has duplicate bones (first encountered: %s)" % bone.name)
                break

            names.add(bone.name.lower())

        return result

    def has_valid_hierarchy(self) -> ValidatorResult:
        result = ValidatorResult()

        bones = self.skeleton.bones
        bone_order = {}
        for bone in bones:
            if bone.parent != "" and bone.parent not in bone_order:
                result.set(
                    False,
                    "skeleton has invalid bone hierarchy (first invalid bone encountered: %s)" % bone.name
                )
                break

            bone_order[bone.name] = bone.parent

        return result

    def only_ascii_bones(self) -> ValidatorResult:
        result = ValidatorResult()

        for bone in self.skeleton.bones:
            if not self.is_ascii_internal(bone.name) or not self.is_ascii_internal(bone.parent):
                result.set(False, "skeleton has bones with non-ASCII characters (first encountered: %s)" % bone.name)
                break

        return result


class ValidatorSkeletonGeneric(ValidatorComponentSkeleton):
    """Skeleton - Generic"""

    def conditions(self) -> tuple[
        tuple[ValidatorFunctionType, ...],
        tuple[ValidatorFunctionType, ...],
        tuple[ValidatorFunctionType, ...]
    ]:
        strict = (
            self.has_valid_name,
            self.only_unique_bones,
            self.has_valid_hierarchy,
            self.only_ascii_bones
        )
        optional = info = ()

        return strict, optional, info


class ValidatorSkeletonRTM(ValidatorComponentSkeleton):
    """Skeleton - RTM"""

    def has_rtm_compatible_bones(self) -> ValidatorResult:
        result = ValidatorResult()

        for bone in self.skeleton.bones:
            if len(bone.name) > 31 or len(bone.parent) > 31:
                result.set(False, "skeleton has bone names longer than 31 characters")
                break

        return result

    def conditions(self) -> tuple[
        tuple[ValidatorFunctionType, ...],
        tuple[ValidatorFunctionType, ...],
        tuple[ValidatorFunctionType, ...]
    ]:
        strict = (
            self.has_rtm_compatible_bones,
        )
        optional = info = ()

        return strict, optional, info


class SkeletonValidator(Validator):
    def validate(
        self,
        skeleton: Any,
        for_rtm: bool = False,
        lazy: bool = False
    ) -> bool:
        self.logger.start_subproc("Validating %s" % skeleton.name)

        is_valid = True
        components: list[type[ValidatorComponentSkeleton]] = [ValidatorSkeletonGeneric]
        if for_rtm:
            components.append(ValidatorSkeletonRTM)

        for item in components:
            is_valid &= item(skeleton, self.logger).validate(lazy, False)

        self.logger.step("Validation %s" % ("PASSED" if is_valid else "FAILED"))
        self.logger.end_subproc()
        self.logger.step("Finished validation")

        return is_valid
