from typing import Literal, TypeAlias, Protocol
from collections.abc import Callable

import bpy


OperatorReturn: TypeAlias = set[
    Literal[
        "RUNNING_MODAL",
        "CANCELLED",
        "FINISHED",
        "PASS_THROUGH",
        "INTERFACE"
    ]
]

OperatorReportType: TypeAlias = set[
    Literal[
        "DEBUG",
        "INFO",
        "OPERATOR",
        "PROPERTY",
        "WARNING",
        "ERROR",
        "ERROR_INVALID_INPUT",
        "ERROR_INVALID_CONTEXT",
        "ERROR_OUT_OF_MEMORY"
    ]
]


Registerable: TypeAlias = type[
    bpy.types.Panel
    | bpy.types.UIList
    | bpy.types.Menu
    | bpy.types.Header
    | bpy.types.Operator
    | bpy.types.KeyingSetInfo
    | bpy.types.RenderEngine
    | bpy.types.AssetShelf
    | bpy.types.FileHandler
    | bpy.types.AddonPreferences
    | bpy.types.PropertyGroup
]


class RegisterableModule(Protocol):
    register: Callable[[], None]
    unregister: Callable[[], None]
