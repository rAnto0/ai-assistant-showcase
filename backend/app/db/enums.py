from enum import Enum


class CatalogStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class ChatChannel(str, Enum):
    WIDGET = "WIDGET"
    TELEGRAM = "TELEGRAM"


class ChatMessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class LeadSource(str, Enum):
    WIDGET = "WIDGET"
    TELEGRAM = "TELEGRAM"
