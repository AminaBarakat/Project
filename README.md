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
| `storage.py` | Saves tournaments: SQLite while developing locally, Supabase after deployment |
| `screens/home.py` | Create a tournament / join with a code |
| `screens/lobby.py` | The waiting room. Refreshes every 2 seconds |
| `round1.py` | Round 1 rules: the four games, the random draw of games, the 60-second timer, tie-breakers, results |
| `screens/round1.py` | Round 1 on each phone: intro, the duel's game, waiting room, tie-breaker, results |
| `screens/art.py` | The drawings for the four games (objects, rooms, tiles, padlock), made in code as SVG |
| `screens/duels.py` | The list of duels (shown in the Round 1 intro) |
| `screens/round2.py` | Placeholder showing who's still in |
| `screens/common.py` | Shared bits: title, how a player is shown (avatar slot), messages |
| `tests/` | Tests for the rules and the storage |

## How it works

- **Shared state.** Each phone runs its own copy of the screens, so the tournament can't live in one phone's memory. Locally it lives in `data/game.db`. On the deployed app it lives in Supabase, so every phone reaches the same tournament.
- **Live updates.** The lobby re-reads the database every 2 seconds (`st.fragment(run_every="2s")`), so new players appear on everyone's screen within a couple of seconds.
- **Simultaneous actions.** Updates happen one at a time (`BEGIN IMMEDIATE` in `storage.update`). If two people grab the last seat at once, the first one saved gets it and the other is told the tournament is full. `tests/test_storage.py` checks this with 12 people joining at the same moment.
- **Round 1.** Each of the 4 duels gets a different game, drawn at random (Number Lock, Pattern Wall, Escape Route, Memory Table). Both players in a duel play the same game at the same time, with one try. After a 5-second intro, the game appears and the 60-second timer starts. The games: **Number Lock** (a 4-digit padlock with five clues), **Pattern Wall** (a 4×4 wall of coloured shapes with one gap), **Escape Route** (13 rooms, 16 possible routes, one safe path) and **Memory Table** (8 objects shown for 6 seconds, then find the 2 that vanished). The tests check that each puzzle has exactly one answer.
- **Who wins a duel.** If only one player is right, they win. If both are right, the faster one wins. If both are wrong or run out of time, there's a 30-second tie-breaker question: the right answer wins, otherwise the faster answer, and if nobody answers, a random draw.
- **Timing without a boss.** No phone is "in charge" of the clock. Every phone calls `round1.settle()` each second, which applies whatever is due (closing games when time is up, deciding duels, starting tie-breakers, showing results, moving on to Round 2 after 8 seconds). Running it twice changes nothing, so it doesn't matter which phone gets there first.
- **Who is who.** When you create or join, you get a random player id that's kept in your page address (`?code=KQZT&me=p_...`). Refreshing the page keeps you in the game. Only the host's id can start the tournament or remove players.

## Known limits

- Anyone who gets hold of your full page address can act as you. There are no accounts. That's fine for a party game, but don't share your address, only the code.
- The lobby refreshes every 2 seconds, not instantly.
- Exactly 8 players for now.

## Put the multiplayer lobby online

1. Create a free Supabase project.
2. In its **SQL Editor**, run the script in `docs/supabase-setup.sql`.
3. In **Project Settings → API**, copy the **Project URL** and the public **anon key**. Do not copy or share the `service_role` key.
4. For local testing, create `.streamlit/secrets.toml` (it is ignored by Git):

   ```toml
   [supabase]
   url = "https://your-project.supabase.co"
   key = "your-public-anon-key"
   ```

5. For deployment, add the same two values under the Streamlit app's **Settings → Secrets**. Then every player uses the shared online lobby.
