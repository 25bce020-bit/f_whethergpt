from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database import Base


class OfficialAlert(Base):

    __tablename__ = "official_alerts"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    identifier: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(255)
    )

    event: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    severity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    urgency: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    certainty: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    headline: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    official: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )