"""Gestione database carte predefinite."""

import json
from pathlib import Path
from .models import Card, CardType, Deck, DeckConfig


DATA_DIR = Path(__file__).parent.parent / "data"
CARDS_FILE = DATA_DIR / "cards.json"


def load_default_cards() -> tuple[list[Card], list[Card]]:
    """Carica le carte predefinite dal database.

    Returns:
        Tuple con (carte_nere, carte_bianche)
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
    """Crea un mazzo con le carte predefinite.

    Args:
        config: Configurazione personalizzata del mazzo

    Returns:
        Mazzo con tutte le carte predefinite
    """
    if config is None:
        config = DeckConfig()

    deck = Deck(config=config)
    black_cards, white_cards = load_default_cards()
    deck.black_cards = black_cards
    deck.white_cards = white_cards

    return deck


def get_cards_count() -> dict:
    """Restituisce il conteggio delle carte nel database."""
    black_cards, white_cards = load_default_cards()
    return {
        "black": len(black_cards),
        "white": len(white_cards),
        "total": len(black_cards) + len(white_cards)
    }
