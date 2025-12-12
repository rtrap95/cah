# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cards Against Humanity card generator with GUI and CLI interfaces. Built with Python 3.13+, customtkinter for the GUI, and SQLite for persistence.

## Commands

```bash
# Run GUI (default)
uv run python main.py

# Run CLI
uv run python main.py --cli

# Or using entry points after install
uv run cah      # GUI
uv run cah-cli  # CLI
```

## Architecture

```
cah/
├── gui.py      # Main GUI application (customtkinter)
├── db.py       # SQLite database layer (decks, cards, settings tables)
├── models.py   # Data models: Card, CardType, Deck, DeckConfig
├── export.py   # PDF export with reportlab
├── cli.py      # Interactive CLI menu (rich/typer)
├── database.py # Legacy JSON loading
└── decks.py    # Deck management utilities
```

**Data flow**: GUI/CLI → db.py → SQLite (`data/cah.db`) → models.py

**Key components**:
- `CAHApp` (gui.py): Main window with sidebar navigation, paginated card grid, dialogs for CRUD operations
- `CardFrame` (gui.py): Clickable card widget with hover effects and index display
- `db.py`: All database operations (CRUD for decks/cards, settings for default deck)
- `export_deck_to_pdf` (export.py): Generates printable PDF with card grids

## Language

UI strings are in English. Card content may be in any language.
