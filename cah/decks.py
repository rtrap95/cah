"""Custom deck management."""

import json
from pathlib import Path
from .models import Deck, DeckConfig, Card, CardType


DECKS_DIR = Path(__file__).parent.parent / "decks"


def ensure_decks_dir():
    """Ensure the decks directory exists."""
    DECKS_DIR.mkdir(exist_ok=True)


def list_saved_decks() -> list[dict]:
    """List all saved decks.

    Returns:
        List of dictionaries with deck info
    """
    ensure_decks_dir()
    decks = []

    for deck_file in DECKS_DIR.glob("*.json"):
        try:
            with open(deck_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            decks.append({
                "filename": deck_file.name,
                "path": deck_file,
                "name": data.get("config", {}).get("name", "Unnamed"),
                "short_name": data.get("config", {}).get("short_name", "???"),
                "black_count": len(data.get("black_cards", [])),
                "white_count": len(data.get("white_cards", []))
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return decks


def save_deck(deck: Deck, filename: str | None = None) -> Path:
    """Save a deck to file.

    Args:
        deck: The deck to save
        filename: Optional filename (default: deck_name.json)

    Returns:
        Path of saved file
    """
    ensure_decks_dir()

    if filename is None:
        # Generate filename from deck name
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_"
                          for c in deck.config.name)
        safe_name = safe_name.strip().replace(" ", "_").lower()
        filename = f"{safe_name}.json"

    if not filename.endswith(".json"):
        filename += ".json"

    path = DECKS_DIR / filename
    deck.save(path)
    return path


def load_deck(filename: str) -> Deck:
    """Load a deck from file.

    Args:
        filename: Deck filename

    Returns:
        The loaded deck
    """
    if not filename.endswith(".json"):
        filename += ".json"

    path = DECKS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Deck not found: {filename}")

    return Deck.load(path)


def delete_deck(filename: str) -> bool:
    """Delete a saved deck.

    Args:
        filename: Filename to delete

    Returns:
        True if deleted, False otherwise
    """
    if not filename.endswith(".json"):
        filename += ".json"

    path = DECKS_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False


def create_empty_deck(name: str, short_name: str,
                      logo_path: str | None = None) -> Deck:
    """Create a new empty deck.

    Args:
        name: Full deck name
        short_name: Short name (max 5 characters)
        logo_path: Optional logo path

    Returns:
        New empty deck
    """
    config = DeckConfig(
        name=name,
        short_name=short_name[:5].upper(),
        logo_path=logo_path
    )
    return Deck(config=config)


def add_card_to_deck(deck: Deck, text: str, card_type: CardType,
                     pick: int = 1) -> Card:
    """Add a card to the deck.

    Args:
        deck: The deck
        text: Card text
        card_type: Type (BLACK or WHITE)
        pick: Number of cards to pick (black cards only)

    Returns:
        The created card
    """
    card = Card(text=text, card_type=card_type, pick=pick)
    deck.add_card(card)
    return card


def merge_decks(base_deck: Deck, *other_decks: Deck) -> Deck:
    """Merge multiple decks into one.

    Args:
        base_deck: Base deck (uses its configuration)
        other_decks: Other decks to merge

    Returns:
        New deck with all cards
    """
    merged = Deck(config=base_deck.config)
    merged.black_cards = list(base_deck.black_cards)
    merged.white_cards = list(base_deck.white_cards)

    for deck in other_decks:
        merged.black_cards.extend(deck.black_cards)
        merged.white_cards.extend(deck.white_cards)

    return merged
