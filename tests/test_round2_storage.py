"""Round 2 winner selection is serialized by the shared storage layer."""

import copy
import random
import threading

import round2
import storage

START = 1_000_000.0


def test_only_the_first_concurrent_route_completion_is_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_supabase", None)
    db = tmp_path / "game.db"
    tour, _, _ = storage.create("Host", path=db)

    def prepare(current):
        new = copy.deepcopy(current)
        new["players"].extend(
            {"id": pid, "name": pid, "appearance": None}
            for pid in ("p0", "p1", "p2", "p3")
        )
        new["status"] = "round2"
        new["round2"] = round2.new_round(("p0", "p1", "p2", "p3"), START, random.Random(2))
        for duo in new["round2"]["duos"].values():
            duo["code_solved_at"] = START + 1
            duo["route_step"] = 1
        return new, "Round 2 prepared."

    storage.update(tour["code"], prepare, path=db)
    current = storage.load(tour["code"], path=db)
    duos = list(current["round2"]["duos"])
    actions = []
    for duo_id in duos:
        player_id = current["round2"]["duos"][duo_id]["players"][0]
        actions.append((player_id, duo_id))

    messages = []
    barrier = threading.Barrier(2)

    def finish(player_id, duo_id):
        barrier.wait()
        _, message = storage.update(
            tour["code"], round2.choose_door, player_id, duo_id, "Rooftop", START + 2, path=db
        )
        messages.append(message)

    threads = [threading.Thread(target=finish, args=action) for action in actions]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final = storage.load(tour["code"], path=db)
    assert final["status"] == "final"
    assert final["round2"]["winner"] in duos
    assert sum("advances" in message for message in messages) == 1
    assert sum("already won" in message for message in messages) == 1
