"""Modelli dati per le carte."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
from pathlib import Path


class CardType(Enum):
    """Tipo di carta."""
    BLACK = "black"  # Carte domanda (nere)
    WHITE = "white"  # Carte risposta (bianche)


@dataclass
class Card:
    """Rappresenta una singola carta."""
    text: str
    card_type: CardType
    pick: int = 1  # Numero di carte bianche da scegliere (solo per carte nere)
    id: Optional[int] = None  # ID database

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "card_type": self.card_type.value,
            "pick": self.pick
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(
            text=data["text"],
            card_type=CardType(data["card_type"]),
            pick=data.get("pick", 1)
        )


@dataclass
class DeckConfig:
    """Configurazione personalizzata del mazzo."""
    name: str = "Cards Against Humanity"
    short_name: str = "CAH"
    logo_path: Optional[str] = None
    primary_color: str = "#000000"
    secondary_color: str = "#FFFFFF"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "short_name": self.short_name,
            "logo_path": self.logo_path,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeckConfig":
        return cls(**data)


@dataclass
class Deck:
    """Rappresenta un mazzo di carte personalizzato."""
    config: DeckConfig
    black_cards: list[Card] = field(default_factory=list)
    white_cards: list[Card] = field(default_factory=list)
    id: Optional[int] = None  # ID database

    def add_card(self, card: Card) -> None:
        if card.card_type == CardType.BLACK:
            self.black_cards.append(card)
        else:
            self.white_cards.append(card)

    def remove_card(self, card: Card) -> bool:
        target_list = self.black_cards if card.card_type == CardType.BLACK else self.white_cards
        if card in target_list:
            target_list.remove(card)
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "black_cards": [c.to_dict() for c in self.black_cards],
            "white_cards": [c.to_dict() for c in self.white_cards]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Deck":
        deck = cls(config=DeckConfig.from_dict(data["config"]))
        deck.black_cards = [Card.from_dict(c) for c in data.get("black_cards", [])]
        deck.white_cards = [Card.from_dict(c) for c in data.get("white_cards", [])]
        return deck

    def save(self, path: Path) -> None:
        """Salva il mazzo su file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Deck":
        """Carica un mazzo da file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @property
    def total_cards(self) -> int:
        return len(self.black_cards) + len(self.white_cards)
