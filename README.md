# The Missing Mastermind

A multiplayer mystery tournament for 5 or 8 players, each on their own device. One player creates a tournament and shares a 4-letter code. Friends join, the host starts the game, and players complete puzzle rounds until one champion remains.

Team project for Introduction to Programming (Nova SBE, 2026/27).

**Play it:** https://missing-mastermind.streamlit.app/

## Team

| Name | Student number |
| Amina Barakat | 73376 |
| Marta Sofia Lourenço Neves | 56476 |
| Asia Ferrari | 74000 |
| Eleonora Ripa | 65608 |

## Objectives

The Missing Mastermind turns the social experience of a board-game mystery into an online multiplayer game.

The project aims to:

- Create a fun, interactive game for friends on different devices, with customisable detective avatars.
- Test logic, observation, memory, speed, and problem-solving skills.
- Encourage teamwork and communication in the cooperative round.
- Let eliminated players stay involved by sending reactions and voting for the fan favourite at the end of the game.
- Use Python, Streamlit, and shared online storage to build a real-time multiplayer experience.

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
| `round1.py` | Round 1 rules: puzzle banks, game order, timers, scoring, tie-breakers, and results |
| `screens/round1.py` | Round 1 on each phone: intro, the four games one after another, waiting room, tie-breaker, results |
| `screens/art.py` | The drawings for the four games (objects, rooms, tiles, padlock), made in code as SVG, and the "tap the picture" buttons |
| `screens/duels.py` | The list of duels (shown in the Round 1 intro) |
| `round2.py` | Round 2 rules: private clue cards, code, route, lockout, timer and winner |
| `screens/round2.py` | Round 2 screen, refreshed from shared storage every 2 seconds |
| `round3.py` | Round 3 rules: the final mansion mystery, theories, timer, and winner |
| `screens/round3.py` | Round 3 on each phone: clues, theory form, and final code reveal |
| `screens/common.py` | Shared bits: title, how a player is shown (avatar slot), messages |
| `tests/` | Tests for the rules and the storage |

## How it works

- **Shared state.** Each phone runs its own copy of the screens, so the tournament can't live in one phone's memory. Locally it lives in `data/game.db`. On the deployed app it lives in Supabase, so every phone reaches the same tournament.
- **Live updates.** The lobby and Round 2 re-read the database every 2 seconds (`st.fragment(run_every="2s")`), so each phone sees shared progress shortly after an action.
- **Simultaneous actions.** Updates happen one at a time (`BEGIN IMMEDIATE` in `storage.update`). If two people grab the last seat at once, the first one saved gets it and the other is told the tournament is full. `tests/test_storage.py` checks this with 12 people joining at the same moment.
- **Player modes and Round 1.** The host can create a game for either 5 or 8 players. With 8 players, Round 1 is played through four 1 v 1 duels. With 5 players, everyone competes at the same time and the lowest-scoring detective is eliminated, leaving four players for Round 2.
- **Round 1.** Round 1 includes four fast-paced puzzle games: **Number Lock**, where players solve clues to open a four-digit padlock; **Pattern Wall**, where they identify the missing coloured shape; **Escape Route**, where they follow clues to find the safe route through a map; and **Memory Table**, where they remember objects and identify the ones that disappeared. Each game has several possible versions, so every tournament feels different. Players must think quickly, choose an answer, and lock it in before time runs out.
- **Round 2.** When Round 1 results end, its remaining detectives are paired into two duos. Each player sees only their own clue card and can share it with their teammate in order to solve the code. Code, route, alarms and the winner are stored in the shared tournament record. The winning duo's two players advance to Round 3.
- **Waiting room and host.** Players who are done watch one animated race track with every detective's token sliding along as they get through their games (it never shows right or wrong). The host also gets two controls there: mark a player who has left the game (their opponent goes through), or end the round now (every unfinished game counts as not answered).
- **Colour-blind friendly.** On the Pattern Wall each colour also has its own texture (dots, stripes, lines, plain), so tiles can be told apart without colour.
- **Who wins a duel.** More right answers wins. With the same number right, the faster total time wins. If both got nothing right, there's a 30-second tie-breaker question: the right answer wins, otherwise the faster answer, and if nobody answers, a random draw. When everyone has finished, the results appear straight away, without waiting for any timer.
- **Timing without a boss.** No phone is "in charge" of the clock. Every phone calls the active round's `settle()` function, which applies whatever is due. Round 1 moves on after 10 seconds of results; Round 2 uses a server-stored one-minute timer. Running settlement twice changes nothing, so it doesn't matter which phone gets there first.
- **Who is who.** When you create or join, you get a random player id that's kept in your page address (`?code=KQZT&me=p_...`). Refreshing the page keeps you in the game. Only the host's id can start the tournament or remove players.
- **Joining and sharing.** The host can share the four-letter game code or a QR code, so friends can join quickly from their own phones.
- **Leaving a game.** A player can leave the tournament if needed. The host can also mark a missing player as having left, allowing the game to continue without them.

## Known limits

- Anyone who gets hold of the host's full page address can act as the host as there is no accounts creation on this game.
- The lobby refreshes every 2 seconds, not instantly.
- Games can currently be created for either 5 or 8 players.

## Put the multiplayer lobby online

1. Create a free Supabase project.
2. In its **SQL Editor**, run the script in `docs/supabase-setup.sql`.
3. In **Project Settings → API**, copy the **Project URL** and the key used by your Supabase setup. Store it only in Streamlit's server-side Secrets; never put it in code or send it to a browser.

> Never commit `secrets.toml` or paste a real Supabase key into GitHub.

4. For local testing, add these values to `.streamlit/secrets.toml` (it is ignored by Git):

   ```toml
   [supabase]
   url = "https://your-project.supabase.co"
   key = "your-supabase-key"
   ```

5. For deployment, add the same two values under the Streamlit app's **Settings → Secrets**. Then every player uses the shared online lobby.
