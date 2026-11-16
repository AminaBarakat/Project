# Notes for coding agents

Team project (3–4 beginner programmers) for Introduction to Programming, Nova SBE. A multiplayer mystery tournament: 8 players, each on their own phone, built with Python + Streamlit. Read `README.md` first ("Where things are" and "How it works").

## Running things

- App: `uv run streamlit run app.py`. Tests: `uv run pytest`. Never use `pip` or `python -m venv`.
- New libraries only if truly needed, pinned with `==` in `pyproject.toml`, and the student must agree first.

## Ground rules for this code

- Rules go in plain Python modules (like `tournament.py`) that know nothing about Streamlit. Screens in `screens/` call them, and so do the tests.
- Rule functions take the tournament dict and return `(new_tournament, message)`. A refused action returns the tournament unchanged plus a reason. Never modify the dict you were given.
- All shared data goes through `storage.py`. Changes use `storage.update(code, action, ...)` so they happen one at a time. Never keep shared game data in `st.session_state`; that is only for this phone.
- Anything only the host may do must check `is_host` inside the rule function, not just hide a button.
- Player names are user input. Show them through `common.safe()` / `common.player_label()`. Never put them in HTML with `unsafe_allow_html=True` without `html.escape()`.

## How to work

- Work on a branch per task, never directly on `main`. Changes reach `main` through a reviewed pull request.
- New rules come with tests, including the refused cases. Run `uv run pytest` and paste the output as proof.
- Don't change or delete existing tests to make them pass. If one looks wrong, say so and stop.
- The students are beginners and must explain the whole project in a walkthrough. Explain what you changed, with file and line.
