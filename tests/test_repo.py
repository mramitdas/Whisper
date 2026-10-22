from bot.db import repo


async def test_upsert_user_inserts_then_updates(db):
    await repo.upsert_user(db, 1, "amy", "Amy", "en")
    u = await repo.get_user(db, 1)
    assert u is not None
    assert u.username == "amy" and u.first_name == "Amy"
    await repo.upsert_user(db, 1, "amy2", "Amy L", "en")
    u = await repo.get_user(db, 1)
    assert u is not None
    assert u.username == "amy2"
    assert await repo.count_users(db) == 1


async def test_reports_and_unique_reporters(db):
    await repo.add_report(db, reporter=10, target=20, reason="spam", session_ref="s1")
    await repo.add_report(db, reporter=11, target=20, reason="abuse", session_ref="s1")
    await repo.add_report(db, reporter=10, target=20, reason="spam again", session_ref="s2")
    assert await repo.unique_reporters(db, 20) == 2
    assert await repo.count_reports(db) == 3


async def test_ban_lifecycle(db):
    await repo.add_ban(db, 30, "auto: reports")
    assert await repo.get_ban(db, 30) is not None
    await repo.remove_ban(db, 30)
    assert await repo.get_ban(db, 30) is None


async def test_counters(db):
    await repo.upsert_user(db, 1, None, "A", None)
    await repo.record_match(db)
    assert await repo.count_users(db) == 1
    assert await repo.count_matches(db) == 1
