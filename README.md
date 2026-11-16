# The Missing Mastermind

*Working title.* A multiplayer mystery tournament for 8 players, each on their own phone. One player creates a tournament and shares a 4-letter code. Seven friends join, and the host starts. Players are drawn into random 1 v 1 duels, and puzzle rounds knock players out until one champion remains.

Team project for Introduction to Programming (Nova SBE, 2026/27).

**Play it:** _deployed URL goes here_

## Team

| Name | Student number |
|------|----------------|
| | |
| | |
| | |
| | |

## Run it

```
uv run streamlit run app.py
```

`uv` installs Python and the libraries by itself the first time.

**Trying it with several players on one computer:** open the app in a few browser windows (use private/incognito windows too). Each window is a different player.

**Trying it with phones:** when the app starts, the terminal shows a *Network URL* (like `http://192.168.1.20:8501`). Phones on the same Wi-Fi can open that address.

## Test it

```
uv run pytest
```

## Where things are

| File | What it does |
|------|--------------|
| `app.py` | Start here. Decides which screen to show |
| `tournament.py` | The rules: create, join, leave, remove, start, and the random duel draw |
| `storage.py` | Saves tournaments in a shared SQLite database (`data/game.db`) so all phones see the same game |
| `screens/home.py` | Create a tournament / join with a code |
| `screens/lobby.py` | The waiting room. Refreshes every 2 seconds |
| `screens/duels.py` | The Round 1 duels after the host starts |
| `screens/common.py` | Shared bits: title, how a player is shown (avatar slot), messages |
| `tests/` | Tests for the rules and the storage |

## How it works

- **Shared state.** Each phone runs its own copy of the screens, so the tournament can't live in one phone's memory. It lives in `data/game.db`, and every screen reads it from there.
- **Live updates.** The lobby re-reads the database every 2 seconds (`st.fragment(run_every="2s")`), so new players appear on everyone's screen within a couple of seconds.
- **Simultaneous actions.** Updates happen one at a time (`BEGIN IMMEDIATE` in `storage.update`). If two people grab the last seat at once, the first one saved gets it and the other is told the tournament is full. `tests/test_storage.py` checks this with 12 people joining at the same moment.
- **Who is who.** When you create or join, you get a random player id that's kept in your page address (`?code=KQZT&me=p_...`). Refreshing the page keeps you in the game. Only the host's id can start the tournament or remove players.

## Known limits

- Anyone who gets hold of your full page address can act as you. There are no accounts. That's fine for a party game, but don't share your address, only the code.
- On a free host the disk can be wiped when the app restarts, which ends any tournament in progress.
- The lobby refreshes every 2 seconds, not instantly.
- Exactly 8 players for now.
