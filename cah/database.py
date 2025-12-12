"""Default cards database management."""

import json
from pathlib import Path
from .models import Card, CardType, Deck, DeckConfig


DATA_DIR = Path(__file__).parent.parent / "data"
CARDS_FILE = DATA_DIR / "cards.json"


def load_default_cards() -> tuple[list[Card], list[Card]]:
    """Load default cards from database.

    Returns:
        Tuple with (black_cards, white_cards)
    """
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    black_cards = [
        Card(
            text=c["text"],
            card_type=CardType.BLACK,
            pick=c.get("pick", 1)
        )
        for c in data.get("black_cards", [])
    ]

    white_cards = [
        Card(
            text=c["text"],
            card_type=CardType.WHITE,
            pick=1
        )
        for c in data.get("white_cards", [])
    ]

    return black_cards, white_cards


def create_default_deck(config: DeckConfig | None = None) -> Deck:
    """Create a deck with default cards.

    Args:
        config: Custom deck configuration

    Returns:
        Deck with all default cards
    """
    if config is None:
        config = DeckConfig()

    deck = Deck(config=config)
    black_cards, white_cards = load_default_cards()
    deck.black_cards = black_cards
    deck.white_cards = white_cards

    return deck


def get_cards_count() -> dict:
    """Return the card count in the database."""
    black_cards, white_cards = load_default_cards()
    return {
        "black": len(black_cards),
        "white": len(white_cards),
        "total": len(black_cards) + len(white_cards)
    }
