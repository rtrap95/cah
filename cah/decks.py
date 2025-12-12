"""Gestione mazzi personalizzati."""

import json
from pathlib import Path
from .models import Deck, DeckConfig, Card, CardType


DECKS_DIR = Path(__file__).parent.parent / "decks"


def ensure_decks_dir():
    """Assicura che la directory dei mazzi esista."""
    DECKS_DIR.mkdir(exist_ok=True)


def list_saved_decks() -> list[dict]:
    """Elenca tutti i mazzi salvati.

    Returns:
        Lista di dizionari con info sui mazzi
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
                "name": data.get("config", {}).get("name", "Senza nome"),
                "short_name": data.get("config", {}).get("short_name", "???"),
                "black_count": len(data.get("black_cards", [])),
                "white_count": len(data.get("white_cards", []))
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return decks


def save_deck(deck: Deck, filename: str | None = None) -> Path:
    """Salva un mazzo su file.

    Args:
        deck: Il mazzo da salvare
        filename: Nome file opzionale (default: nome_mazzo.json)

    Returns:
        Percorso del file salvato
    """
    ensure_decks_dir()

    if filename is None:
        # Genera nome file dal nome del mazzo
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
    """Carica un mazzo da file.

    Args:
        filename: Nome del file del mazzo

    Returns:
        Il mazzo caricato
    """
    if not filename.endswith(".json"):
        filename += ".json"

    path = DECKS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Mazzo non trovato: {filename}")

    return Deck.load(path)


def delete_deck(filename: str) -> bool:
    """Elimina un mazzo salvato.

    Args:
        filename: Nome del file da eliminare

    Returns:
        True se eliminato, False altrimenti
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
    """Crea un nuovo mazzo vuoto.

    Args:
        name: Nome completo del mazzo
        short_name: Nome breve (max 5 caratteri)
        logo_path: Percorso opzionale al logo

    Returns:
        Nuovo mazzo vuoto
    """
    config = DeckConfig(
        name=name,
        short_name=short_name[:5].upper(),
        logo_path=logo_path
    )
    return Deck(config=config)


def add_card_to_deck(deck: Deck, text: str, card_type: CardType,
                     pick: int = 1) -> Card:
    """Aggiunge una carta al mazzo.

    Args:
        deck: Il mazzo
        text: Testo della carta
        card_type: Tipo (BLACK o WHITE)
        pick: Numero di carte da pescare (solo per carte nere)

    Returns:
        La carta creata
    """
    card = Card(text=text, card_type=card_type, pick=pick)
    deck.add_card(card)
    return card


def merge_decks(base_deck: Deck, *other_decks: Deck) -> Deck:
    """Unisce più mazzi in uno.

    Args:
        base_deck: Mazzo base (usa la sua configurazione)
        other_decks: Altri mazzi da unire

    Returns:
        Nuovo mazzo con tutte le carte
    """
    merged = Deck(config=base_deck.config)
    merged.black_cards = list(base_deck.black_cards)
    merged.white_cards = list(base_deck.white_cards)

    for deck in other_decks:
        merged.black_cards.extend(deck.black_cards)
        merged.white_cards.extend(deck.white_cards)

    return merged
