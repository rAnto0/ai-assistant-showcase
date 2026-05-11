from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CatalogChunk:
    text: str
    metadata: dict[str, Any]
