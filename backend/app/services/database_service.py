from sqlalchemy import select

from app.database import (
    AsyncSessionLocal,
)
from datetime import datetime, timezone
from app.models import (
    User,
    Conversation,
    ChatMessage,
    WeatherRecord,
    OfficialAlert,
    IngestionLog,
)


async def create_user(
    name: str | None = None,
    email: str | None = None,
    password_hash: str | None = None,
):

    async with AsyncSessionLocal() as session:

        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
        )

        session.add(user)

        await session.commit()

        await session.refresh(user)

        return user


async def get_user(
    user_id: int,
):

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()


async def get_or_create_conversation(
    session_id: str,
    user_id: int | None = None,
):

    async with AsyncSessionLocal() as session:

        statement = select(Conversation).where(Conversation.session_id == session_id)
        if user_id is None:
            statement = statement.where(Conversation.user_id.is_(None))
        else:
            # A matching guest conversation is deliberately claimed at login;
            # another account's conversation is never reused.
            statement = statement.where(
                (Conversation.user_id == user_id) | Conversation.user_id.is_(None)
            ).order_by(Conversation.user_id.desc().nulls_last())
        result = await session.execute(statement)
        conversation = result.scalars().first()

        if conversation:
            if user_id is not None and conversation.user_id is None:
                conversation.user_id = user_id
                await session.commit()
                await session.refresh(conversation)
            return conversation

        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
        )

        session.add(conversation)

        await session.commit()

        await session.refresh(
            conversation
        )

        return conversation


async def save_chat_message(
    session_id: str,
    role: str,
    content: str,
    tool_used: str | None = None,
    user_id: int | None = None,
):

    conversation = (
        await get_or_create_conversation(
            session_id,
            user_id,
        )
    )

    async with AsyncSessionLocal() as session:

        message = ChatMessage(
            conversation_id=conversation.id,
            role=role,
            content=content,
            tool_used=tool_used,
        )

        session.add(message)

        await session.commit()

        await session.refresh(message)

        return message


async def save_weather_record(
    source: str,
    location_name: str,
    latitude: float,
    longitude: float,
    temperature_c=None,
    apparent_temperature_c=None,
    humidity_percent=None,
    precipitation_mm=None,
    wind_speed_kmh=None,
    weather_code=None,
    observed_at=None,
):

    async with AsyncSessionLocal() as session:

        record = WeatherRecord(
            source=source,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            temperature_c=temperature_c,
            apparent_temperature_c=(
                apparent_temperature_c
            ),
            humidity_percent=(
                humidity_percent
            ),
            precipitation_mm=(
                precipitation_mm
            ),
            wind_speed_kmh=(
                wind_speed_kmh
            ),
            weather_code=weather_code,
            observed_at=observed_at,
        )

        session.add(record)

        await session.commit()

        return record


async def save_official_alert(
    alert: dict,
):

    identifier = alert.get(
        "identifier"
    )

    if not identifier:
        return None

    sent_at = alert.get(
        "sent"
    )

    if isinstance(
        sent_at,
        str,
    ):
        try:

            sent_at = datetime.fromisoformat(
                sent_at.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:

            sent_at = None

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(OfficialAlert).where(
                OfficialAlert.identifier
                == identifier
            )
        )

        existing = (
            result.scalar_one_or_none()
        )

        if existing:
            return existing
        if sent_at is not None and sent_at.tzinfo is not None:
            sent_at = sent_at.astimezone(timezone.utc).replace(tzinfo=None)
        record = OfficialAlert(
            identifier=identifier,
            source=alert.get(
                "source",
                "India Meteorological Department",
            ),
            event=alert.get(
                "event"
            ),
            severity=alert.get(
                "severity"
            ),
            urgency=alert.get(
                "urgency"
            ),
            certainty=alert.get(
                "certainty"
            ),
            headline=alert.get(
                "headline"
            ),
            description=alert.get(
                "description"
            ),
            official=True,
            sent_at=sent_at,
        )

        session.add(record)

        await session.commit()

        await session.refresh(
            record
        )

        return record


async def save_ingestion_log(
    source: str,
    status: str,
    message: str | None = None,
):

    async with AsyncSessionLocal() as session:

        log = IngestionLog(
            source=source,
            status=status,
            message=message,
        )

        session.add(log)

        await session.commit()

        return log
