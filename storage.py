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
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import tournament as rules

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "game.db")

# Join codes use letters that are hard to mix up on a phone (no I/O/L, no 0/1).
CODE_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ"
CODE_LENGTH = 4


# SQLite is ideal while developing on one laptop.  A deployed multiplayer game
# needs one database that every visitor can reach, so app.py can switch this
# module to Supabase by calling configure_supabase().  The rest of the app keeps
# calling create/load/update in exactly the same way.
_supabase = None


class SupabaseError(RuntimeError):
    """A helpful message when the online database cannot be reached."""


class _SupabaseStore:
    """Very small wrapper around Supabase's database HTTP API.

    We deliberately use Python's built-in HTTP tools rather than another
    package.  That keeps the beginner project small and makes the requests
    easy to explain.  The table schema lives in docs/supabase-setup.sql.
    """

    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.key = key

    def _request(self, method, query="", body=None, prefer=None):
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer
        request = Request(
            f"{self.url}/rest/v1/tournaments{query}",
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=10) as response:
                text = response.read().decode()
        except HTTPError as error:
            detail = error.read().decode()
            raise SupabaseError(f"Supabase could not save the game ({error.code}): {detail}") from error
        except OSError as error:
            raise SupabaseError("Supabase could not be reached. Check the project URL and internet connection.") from error
        return json.loads(text) if text else []

    @staticmethod
    def _query(**values):
        return "?" + urlencode(values)

    def create(self, tournament):
        # A duplicate code is extremely unlikely, but the database still gets
        # the final say.  The caller simply tries a different code.
        try:
            rows = self._request("POST", body={"code": tournament["code"], "data": tournament, "version": 0},
                                 prefer="return=representation")
        except SupabaseError as error:
            if "409" in str(error):
                return False
            raise
        return bool(rows)

    def load_row(self, code):
        rows = self._request("GET", self._query(code=f"eq.{code}", select="data,version"))
        return rows[0] if rows else None

    def save_if_current(self, code, version, tournament):
        rows = self._request(
            "PATCH",
            self._query(code=f"eq.{code}", version=f"eq.{version}"),
            body={"data": tournament, "version": version + 1},
            prefer="return=representation",
        )
        return bool(rows)


def configure_supabase(url, key):
    """Use Supabase through the configured key from Streamlit secrets.

    The app sends rendered, player-specific screens to browsers; it never sends
    this credential or raw tournament JSON. Database access stays server-side.
    """
    global _supabase
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("The Supabase URL must start with https://")
    if not isinstance(key, str) or not key.strip():
        raise ValueError("The Supabase key is missing.")
    _supabase = _SupabaseStore(url, key)


def using_supabase():
    """True when the deployed app is using the online shared database."""
    return _supabase is not None


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


def create(host_name, path=DB_PATH, appearance=None):
    """Creates a new tournament with a fresh join code.
    Returns (tournament, host_id, message); tournament is None if refused."""
    host_id = new_player_id()
    # `path` is passed only by the tests, so tests always remain local and do
    # not need a Supabase account.
    if _supabase is not None and path == DB_PATH:
        while True:
            code = "".join(secrets.choice(CODE_LETTERS) for _ in range(CODE_LENGTH))
            tour, message = rules.new_tournament(code, host_id, host_name, appearance)
            if tour is None:
                return None, None, message
            if _supabase.create(tour):
                return tour, host_id, message

    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        while True:
            code = "".join(secrets.choice(CODE_LETTERS) for _ in range(CODE_LENGTH))
            if not conn.execute("SELECT 1 FROM tournaments WHERE code = ?", (code,)).fetchone():
                break
        tour, message = rules.new_tournament(code, host_id, host_name, appearance)
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
    if _supabase is not None and path == DB_PATH:
        row = _supabase.load_row(normalise_code(code))
        return row["data"] if row else None

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
    if _supabase is not None and path == DB_PATH:
        code = normalise_code(code)
        # Compare-and-save is the online equivalent of SQLite's lock below.
        # If another player saved first, we read their newer tournament and try
        # the rule again.  That means the rule, not timing, decides the result.
        for _ in range(5):
            row = _supabase.load_row(code)
            if not row:
                return None, "There's no tournament with that code."
            before = row["data"]
            after, message = action(before, *args)
            if after == before:
                return after, message
            if _supabase.save_if_current(code, row["version"], after):
                return after, message
        return None, "Another player changed this tournament. Please try again."

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
