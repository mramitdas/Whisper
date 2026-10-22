from whisper.config import Settings


def test_defaults_and_types(tmp_path):
    env = tmp_path / ".env"
    env.write_text("BOT_TOKEN=123:abc\nOWNER_ID=42\n")
    s = Settings(_env_file=env)
    assert s.bot_token == "123:abc"
    assert s.owner_id == 42
    assert s.match_timeout_sec == 60
    assert s.session_ttl_sec == 86400
    assert s.max_reports_ban == 5


def test_env_overrides(tmp_path):
    env = tmp_path / ".env"
    env.write_text("BOT_TOKEN=123:abc\nOWNER_ID=42\nMATCH_TIMEOUT_SEC=30\n")
    s = Settings(_env_file=env)
    assert s.match_timeout_sec == 30


def test_forbidden_words_comma_separated(tmp_path):
    env = tmp_path / ".env"
    env.write_text('BOT_TOKEN=123:abc\nOWNER_ID=42\nFORBIDDEN_WORDS="scam, nudes"\n')
    s = Settings(_env_file=env)
    assert s.forbidden_words == ["scam", "nudes"]


def test_forbidden_words_json_list(tmp_path):
    import json

    env = tmp_path / ".env"
    env.write_text(
        "BOT_TOKEN=123:abc\nOWNER_ID=42\n"
        + f"FORBIDDEN_WORDS={json.dumps(['bad', 'ugly'])}\n"
    )
    s = Settings(_env_file=env)
    assert s.forbidden_words == ["bad", "ugly"]
