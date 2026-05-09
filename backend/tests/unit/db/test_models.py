from app.db import models
from app.db.enums import CatalogStatus, ChatChannel, ChatMessageRole, LeadSource
from app.db.postgres import Base


def test_models_register_expected_tables():
    assert set(Base.metadata.tables) == {
        "tenants",
        "catalogs",
        "chat_sessions",
        "chat_messages",
        "leads",
    }
    assert models.Tenant.__tablename__ == "tenants"
    assert models.Catalog.__tablename__ == "catalogs"
    assert models.ChatSession.__tablename__ == "chat_sessions"
    assert models.ChatMessage.__tablename__ == "chat_messages"
    assert models.Lead.__tablename__ == "leads"


def test_enum_values_match_database_contract():
    assert [status.value for status in CatalogStatus] == [
        "UPLOADED",
        "PROCESSING",
        "INDEXED",
        "FAILED",
    ]
    assert [channel.value for channel in ChatChannel] == ["WIDGET", "TELEGRAM"]
    assert [role.value for role in ChatMessageRole] == ["USER", "ASSISTANT", "SYSTEM"]
    assert [source.value for source in LeadSource] == ["WIDGET", "TELEGRAM"]
