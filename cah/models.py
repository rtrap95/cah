"""Data models for cards."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
from pathlib import Path


class CardType(Enum):
    """Card type."""
    BLACK = "black"  # Question cards (black)
    WHITE = "white"  # Answer cards (white)


@dataclass
class Card:
    """Represents a single card."""
    text: str
    card_type: CardType
    pick: int = 1  # Number of white cards to pick (black cards only)
    id: Optional[int] = None  # Database ID

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
    """Custom deck configuration."""
    name: str = "Cards Against Humanity"
    short_name: str = "CAH"
    black_logo_path: Optional[str] = None
    white_logo_path: Optional[str] = None
    primary_color: str = "#000000"
    secondary_color: str = "#FFFFFF"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "short_name": self.short_name,
            "black_logo_path": self.black_logo_path,
            "white_logo_path": self.white_logo_path,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeckConfig":
        return cls(**data)


@dataclass
class Deck:
    """Represents a custom card deck."""
    config: DeckConfig
    black_cards: list[Card] = field(default_factory=list)
    white_cards: list[Card] = field(default_factory=list)
    id: Optional[int] = None  # Database ID

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
        """Save deck to file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Deck":
        """Load deck from file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @property
    def total_cards(self) -> int:
        return len(self.black_cards) + len(self.white_cards)
