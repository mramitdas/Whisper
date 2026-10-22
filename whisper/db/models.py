from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from whisper.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(nullable=True)
    first_name: Mapped[str | None] = mapped_column(nullable=True)
    lang_code: Mapped[str | None] = mapped_column(nullable=True)
    matches: Mapped[int] = mapped_column(default=0)


class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(BigInteger, index=True)
    reported_id: Mapped[int] = mapped_column(BigInteger, index=True)
    reason: Mapped[str] = mapped_column(Text)
    session_ref: Mapped[str | None] = mapped_column(nullable=True)


class Ban(Base, TimestampMixin):
    __tablename__ = "bans"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reason: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Stat(Base):
    __tablename__ = "stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    matches: Mapped[int] = mapped_column(default=0)
