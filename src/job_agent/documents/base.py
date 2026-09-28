"""Shared types for local resume and vacancy documents."""

from dataclasses import dataclass
from datetime import datetime


class DocumentError(ValueError):
    """Raised when a local document cannot be read safely."""


@dataclass(frozen=True, slots=True)
class LocalDocument:
    """Filesystem metadata for a supported local document."""

    name: str
    size: int
    modified_at: datetime
