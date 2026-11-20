"""Tests for screens/live.py: the shared copy used by the parts that refresh every second."""

import storage
from screens import live


def test_phones_share_one_reading_until_it_is_forgotten(monkeypatch):
    reads = []
    monkeypatch.setattr(storage, "load", lambda code, path=None: reads.append(code) or {"code": code, "n": len(reads)})
    live.forget()
    first = live.peek("abcd")
    again = live.peek("ABCD")               # same game, typed differently: still the shared reading
    assert first == again and len(reads) == 1
    live.forget()                           # a full page draw does this
    assert live.peek("ABCD")["n"] == 2 and len(reads) == 2
    live.forget()


def test_changing_the_copy_does_not_change_what_other_phones_see(monkeypatch):
    monkeypatch.setattr(storage, "load", lambda code, path=None: {"code": code, "players": []})
    live.forget()
    live.peek("ABCD")["players"].append("sneaky")
    assert live.peek("ABCD")["players"] == []
    live.forget()
