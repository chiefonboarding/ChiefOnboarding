from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RevokeResult:
    success: bool
    message: str
