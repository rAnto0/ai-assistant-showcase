from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM as PGENUM
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.enums import CatalogStatus, ChatChannel, ChatMessageRole, LeadSource
from app.db.postgres import Base


class Tenant(Base):
    """Business account using the platform.

    Acts as the main data isolation boundary for catalogs, chats, messages, and leads.
    """

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    catalogs: Mapped[list[Catalog]] = relationship(back_populates="tenant")
    chat_sessions: Mapped[list[ChatSession]] = relationship(back_populates="tenant")
    chat_messages: Mapped[list[ChatMessage]] = relationship(back_populates="tenant")
    leads: Mapped[list[Lead]] = relationship(back_populates="tenant")


class Catalog(Base):
    """Uploaded catalog file and its indexing state.

    Tracks CSV/PDF uploads before their parsed chunks are stored in the vector database.
    """

    __tablename__ = "catalogs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[CatalogStatus] = mapped_column(
        PGENUM(CatalogStatus, name="catalog_status"),
        nullable=False,
        default=CatalogStatus.UPLOADED,
    )
    chunks_count: Mapped[int] = mapped_column(nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (Index("ix_catalogs_tenant_id_status", "tenant_id", "status"),)

    tenant: Mapped[Tenant] = relationship(back_populates="catalogs")


class ChatSession(Base):
    """Single conversation between an end user and the AI assistant."""

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    channel: Mapped[ChatChannel] = mapped_column(
        PGENUM(ChatChannel, name="chat_channel"),
        nullable=False,
    )
    external_user_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (Index("ix_chat_sessions_tenant_id_channel", "tenant_id", "channel"),)

    tenant: Mapped[Tenant] = relationship(back_populates="chat_sessions")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    leads: Mapped[list[Lead]] = relationship(back_populates="session")


class ChatMessage(Base):
    """Single message in a chat session.

    Stores user, assistant, and system messages for conversation history.
    """

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[ChatMessageRole] = mapped_column(
        PGENUM(ChatMessageRole, name="chat_message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_chat_messages_session_id_created_at", "session_id", "created_at"),)

    tenant: Mapped[Tenant] = relationship(back_populates="chat_messages")
    session: Mapped[ChatSession] = relationship(back_populates="messages")


class Lead(Base):
    """Potential customer captured from a chat or another channel.

    Stores contact details and the user's expressed interest for follow-up.
    """

    __tablename__ = "leads"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    interest: Mapped[str | None] = mapped_column(Text)
    source: Mapped[LeadSource] = mapped_column(
        PGENUM(LeadSource, name="lead_source"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_leads_tenant_id_source", "tenant_id", "source"),
        UniqueConstraint("tenant_id", "email", name="uq_leads_tenant_id_email"),
    )

    tenant: Mapped[Tenant] = relationship(back_populates="leads")
    session: Mapped[ChatSession | None] = relationship(back_populates="leads")
