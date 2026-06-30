"""Domain models for the speedreader pipeline."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SegmentKind(Enum):
    """The kind of text segment produced by an importer."""

    HEADING = auto()
    PARAGRAPH = auto()
    LIST_ITEM = auto()
    CODE_BLOCK = auto()
    CODE_INLINE = auto()
    BLOCKQUOTE = auto()
    LINK = auto()
    EMPHASIS = auto()
    STRONG = auto()


@dataclass
class TextSegment:
    """A normalized piece of text ready for a reading engine."""

    content: str
    kind: SegmentKind
    level: Optional[int] = None
    language: Optional[str] = None
    metadata: dict = field(default_factory=dict)
