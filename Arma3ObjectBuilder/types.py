from typing import Literal, TypeAlias


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

