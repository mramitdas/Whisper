from whisper.services import moderation

FORBIDDEN = ["scam", "nudes"]


def test_blocks_usernames():
    assert moderation.check_text("hey @someguy123", FORBIDDEN) == "link"
    assert moderation.check_text("hi @ab", FORBIDDEN) is None  # too short for TG username


def test_blocks_urls():
    assert moderation.check_text("check https://evil.com", FORBIDDEN) == "link"
    assert moderation.check_text("go to t.me/spam", FORBIDDEN) == "link"
    assert moderation.check_text("www.foo.com", FORBIDDEN) == "link"
    assert moderation.check_text("plain http://x.io", FORBIDDEN) == "link"


def test_allows_normal_text():
    assert moderation.check_text("3.14 and a@b.co are fine", FORBIDDEN) is None
    assert moderation.check_text("mail contact.site@mail.com", FORBIDDEN) is None
    assert moderation.check_text("version 1.2.3 released", FORBIDDEN) is None
    assert moderation.check_text("awww. so cute", FORBIDDEN) is None


def test_forbidden_words_case_insensitive():
    assert moderation.check_text("Send NUDES please", FORBIDDEN) == "forbidden"
    assert moderation.check_text("this is a scam", FORBIDDEN) == "forbidden"
    assert moderation.check_text("totally normal", FORBIDDEN) is None


def test_empty_word_ignored():
    assert moderation.check_text("hello", ["", "bad"]) is None
