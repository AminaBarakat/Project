"""Shared storage: one place where every phone reads and writes the same tournaments.

Each player's phone runs its own copy of the Streamlit screens, so a tournament kept
in one phone's st.session_state would be invisible to the others. Instead, every
tournament is saved in a small SQLite database file on the server, as JSON.

The rule for simultaneous actions: updates happen ONE AT A TIME. `update()` locks the
database, reads the latest tournament, applies the action, saves, and unlocks. If two
people tap "Join" for the last seat at the same moment, the first one saved gets it
and the second is refused with "This tournament is full".
"""

import json
import os
import secrets
import sqlite3

import tournament as rules

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "game.db")

# Join codes use letters that are hard to mix up on a phone (no I/O/L, no 0/1).
CODE_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ"
CODE_LENGTH = 4


def _connect(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)  # we manage transactions
    conn.execute("CREATE TABLE IF NOT EXISTS tournaments (code TEXT PRIMARY KEY, data TEXT NOT NULL)")
    return conn


def new_player_id():
    """A random id that identifies one player's phone (it ends up in their link)."""
    return "p_" + secrets.token_urlsafe(9)


def normalise_code(code):
    """What the player typed → the stored form ('  kqzt ' → 'KQZT')."""
    return (code or "").strip().upper()


def create(host_name, path=DB_PATH):
    """Creates a new tournament with a fresh join code.
    Returns (tournament, host_id, message); tournament is None if refused."""
    host_id = new_player_id()
    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        while True:
            code = "".join(secrets.choice(CODE_LETTERS) for _ in range(CODE_LENGTH))
            if not conn.execute("SELECT 1 FROM tournaments WHERE code = ?", (code,)).fetchone():
                break
        tour, message = rules.new_tournament(code, host_id, host_name)
        if tour is None:
            conn.execute("ROLLBACK")
            return None, None, message
        conn.execute("INSERT INTO tournaments (code, data) VALUES (?, ?)", (code, json.dumps(tour)))
        conn.execute("COMMIT")
        return tour, host_id, message
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def load(code, path=DB_PATH):
    """The tournament with this code, or None if there isn't one."""
    conn = _connect(path)
    try:
        row = conn.execute("SELECT data FROM tournaments WHERE code = ?", (normalise_code(code),)).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


def update(code, action, *args, path=DB_PATH):
    """Applies one action from tournament.py to the stored tournament, one at a time.

        update("KQZT", rules.join, player_id, "Bruno")

    Returns (tournament, message). If there's no such tournament: (None, message)."""
    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")      # nobody else can write until we COMMIT
        row = conn.execute("SELECT data FROM tournaments WHERE code = ?", (normalise_code(code),)).fetchone()
        if not row:
            conn.execute("ROLLBACK")
            return None, "There's no tournament with that code."
        before = json.loads(row[0])
        after, message = action(before, *args)
        if after != before:
            conn.execute("UPDATE tournaments SET data = ? WHERE code = ?", (json.dumps(after), before["code"]))
        conn.execute("COMMIT")
        return after, message
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
