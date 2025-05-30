from enum import Enum, IntEnum

class RequirementLevel(IntEnum):
    OPTIONAL = 0
    RECOMMENDED = 1
    MANDATORY = 2

    def __str__(self) -> str: return str(self.value)

REQ_LVL_ATTR = "data-hssi-required"