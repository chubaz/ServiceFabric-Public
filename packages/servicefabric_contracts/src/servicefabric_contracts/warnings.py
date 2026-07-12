from typing import Literal
from pydantic import Field
from .common import ContractModel
class ToolWarning(ContractModel):
    code: str = Field(pattern=r"^SF-WARN-[A-Z0-9_]+$")
    message: str = Field(min_length=1, max_length=1000)
    category: Literal["coverage", "evidence", "output", "dependency", "quality"]
    details: dict[str, object] = Field(default_factory=dict, max_length=16)
