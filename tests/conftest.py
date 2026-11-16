"""Shared test setup: make the app modules importable when pytest runs from the project folder."""

import os
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# So that "import logic" works in every test file.
sys.path.insert(0, REPO_DIR)
