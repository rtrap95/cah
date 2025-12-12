# Cards Against Humanity - Generator

Custom card generator for Cards Against Humanity with GUI and CLI interfaces.

> **Note**: This project was created entirely through *vibe coding* with [Claude Code](https://claude.ai/code).

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (package manager)
- macOS: `brew install python-tk@3.13` (for tkinter)

## Installation

```bash
git clone <repo-url>
cd cah
uv sync
```

## Usage

### GUI (default)

```bash
uv run python main.py
```

### CLI

```bash
uv run python main.py --cli
```

## Features

### Deck Management
- Create custom decks with name, abbreviation, and logo
- Load and manage multiple decks
- Set a default deck for startup
- Duplicate existing decks

### Card Management
- Black cards (questions) with multi-pick support (draw 2-3 cards)
- White cards (answers)
- Add single cards or batch import (multiple cards at once)
- Edit and delete cards with a click
- Text search
- Pagination for optimal performance

### Export
- **PDF**: Printable cards in grid format (9 per page)
- **Text**: Copy to clipboard in Markdown format for sharing/AI

### Other Features
- Random combo: displays black card + white cards combination
- Keyboard navigation (arrows to change pages)
- Data persistence with SQLite

## Project Structure

```
cah/
├── gui.py      # Graphical interface (customtkinter)
├── db.py       # SQLite database
├── models.py   # Data models (Card, Deck, DeckConfig)
├── export.py   # PDF generation
├── cli.py      # Command line interface
data/
├── cah.db      # SQLite database
exports/        # Generated PDFs
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← / → | Previous/next page |
| ↑ / ↓ | Vertical scroll |
| Page Up/Down | Fast scroll |
| Home / End | Start/end of list |

## Technologies

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI
- [reportlab](https://www.reportlab.com/) - PDF generation
- [SQLite](https://sqlite.org/) - Database
- [rich](https://github.com/Textualize/rich) / [typer](https://typer.tiangolo.com/) - CLI

## License

[MIT](LICENSE) - Use, modify, and distribute freely.
