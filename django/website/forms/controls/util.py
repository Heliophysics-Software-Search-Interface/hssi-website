from enum import Enum

class RequirementLevel(Enum):
    OPTIONAL = 0
    RECOMMENDED = 1
    MANDATORY = 2

    def __str__(self) -> str: return str(self.value)

REQ_LVL_ATTR = "data-hssi-required"