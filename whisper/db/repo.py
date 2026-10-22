from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from whisper.db.models import Ban, Report, Stat, User


async def upsert_user(db: AsyncSession, uid, username, first_name, lang_code) -> None:
    user = await db.get(User, uid)
    if user is None:
        db.add(User(id=uid, username=username, first_name=first_name, lang_code=lang_code))
    else:
        user.username = username
        user.first_name = first_name
        user.lang_code = lang_code
    await db.flush()


async def get_user(db: AsyncSession, uid) -> User | None:
    return await db.get(User, uid)


async def count_users(db: AsyncSession) -> int:
    return int(await db.scalar(select(func.count()).select_from(User)))


async def add_report(db: AsyncSession, reporter, target, reason, session_ref) -> None:
    db.add(
        Report(
            reporter_id=reporter, reported_id=target, reason=reason, session_ref=session_ref
        )
    )
    await db.flush()


async def unique_reporters(db: AsyncSession, target) -> int:
    q = select(func.count(func.distinct(Report.reporter_id))).where(Report.reported_id == target)
    return int(await db.scalar(q))


async def count_reports(db: AsyncSession) -> int:
    return int(await db.scalar(select(func.count()).select_from(Report)))


async def add_ban(db: AsyncSession, uid, reason) -> None:
    if await db.get(Ban, uid) is None:
        db.add(Ban(user_id=uid, reason=reason))
        await db.flush()


async def remove_ban(db: AsyncSession, uid) -> None:
    ban = await db.get(Ban, uid)
    if ban:
        await db.delete(ban)
        await db.flush()


async def get_ban(db: AsyncSession, uid) -> Ban | None:
    return await db.get(Ban, uid)


async def all_bans(db: AsyncSession) -> list[Ban]:
    return list((await db.scalars(select(Ban))).all())


async def record_match(db: AsyncSession) -> None:
    stat = await db.get(Stat, 1)
    if stat is None:
        db.add(Stat(id=1, matches=1))
    else:
        stat.matches += 1
    await db.flush()


async def count_matches(db: AsyncSession) -> int:
    stat = await db.get(Stat, 1)
    return stat.matches if stat else 0
