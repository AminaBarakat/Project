"""Tests for storage.py. Each test uses its own temporary database (pytest's tmp_path),
so running the tests never touches the real data/game.db."""

import threading

import storage
import tournament as rules


def test_create_then_load_gives_the_same_tournament(tmp_path):
    db = tmp_path / "game.db"
    tour, host_id, _ = storage.create("Ana", path=db)
    assert tour["host_id"] == host_id
    assert len(tour["code"]) == 4
    assert storage.load(tour["code"], path=db) == tour


def test_create_refuses_bad_name_and_saves_nothing(tmp_path):
    db = tmp_path / "game.db"
    tour, host_id, message = storage.create("   ", path=db)
    assert tour is None and host_id is None and message


def test_codes_are_unique_and_easy_to_read(tmp_path):
    db = tmp_path / "game.db"
    codes = {storage.create("Ana", path=db)[0]["code"] for _ in range(50)}
    assert len(codes) == 50
    for code in codes:
        assert all(letter in storage.CODE_LETTERS for letter in code)


def test_load_accepts_lowercase_code_with_spaces(tmp_path):
    db = tmp_path / "game.db"
    tour, _, _ = storage.create("Ana", path=db)
    assert storage.load(f"  {tour['code'].lower()} ", path=db) == tour


def test_unknown_code(tmp_path):
    db = tmp_path / "game.db"
    assert storage.load("ZZZZ", path=db) is None
    tour, message = storage.update("ZZZZ", rules.join, "p1", "Bruno", path=db)
    assert tour is None and message


def test_update_is_saved_and_seen_by_everyone(tmp_path):
    db = tmp_path / "game.db"
    tour, _, _ = storage.create("Ana", path=db)
    storage.update(tour["code"], rules.join, "p1", "Bruno", path=db)
    names = [p["name"] for p in storage.load(tour["code"], path=db)["players"]]
    assert names == ["Ana", "Bruno"]


def test_refused_update_saves_nothing(tmp_path):
    db = tmp_path / "game.db"
    tour, _, _ = storage.create("Ana", path=db)
    _, message = storage.update(tour["code"], rules.join, "p1", "ana", path=db)
    assert "already called" in message
    assert storage.load(tour["code"], path=db) == tour


def test_twelve_people_joining_at_once_fill_exactly_8_seats(tmp_path):
    """The conflict rule: one update at a time, so the 9th to arrive is refused."""
    db = tmp_path / "game.db"
    tour, _, _ = storage.create("Ana", path=db)
    messages = []

    def join(i):
        _, message = storage.update(tour["code"], rules.join, f"p{i}", f"Player {i}", path=db)
        messages.append(message)

    threads = [threading.Thread(target=join, args=(i,)) for i in range(1, 13)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final = storage.load(tour["code"], path=db)
    assert len(final["players"]) == 8
    assert sum("full" in m for m in messages) == 5
