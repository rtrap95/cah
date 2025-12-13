"""SQLite database for data persistence."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
import json

from .models import Card, CardType, Deck, DeckConfig

# Database path
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "cah.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    """Context manager for database operations."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    with db_cursor() as cursor:
        # Decks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                short_name TEXT NOT NULL,
                black_logo_path TEXT,
                white_logo_path TEXT,
                primary_color TEXT DEFAULT '#000000',
                secondary_color TEXT DEFAULT '#FFFFFF',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Cards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                card_type TEXT NOT NULL CHECK(card_type IN ('black', 'white')),
                pick INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_deck ON cards(deck_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(card_type)")

        # Migration: rename logo_path to black_logo_path if old schema exists
        cursor.execute("PRAGMA table_info(decks)")
        columns = [col[1] for col in cursor.fetchall()]
        if "logo_path" in columns and "black_logo_path" not in columns:
            cursor.execute("ALTER TABLE decks RENAME COLUMN logo_path TO black_logo_path")
            cursor.execute("ALTER TABLE decks ADD COLUMN white_logo_path TEXT")


def _seed_default_cards():
    """Load default cards from JSON into database."""
    json_path = DATA_DIR / "cards.json"
    if not json_path.exists():
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Create default deck
    deck_id = create_deck("Cards Against Humanity", "CAH")

    # Insert black cards
    for card_data in data.get("black_cards", []):
        add_card(deck_id, card_data["text"], CardType.BLACK, card_data.get("pick", 1))

    # Insert white cards
    for card_data in data.get("white_cards", []):
        add_card(deck_id, card_data["text"], CardType.WHITE, 1)


def ensure_db():
    """Ensure database exists and is initialized."""
    db_exists = DB_PATH.exists()
    init_db()

    if not db_exists:
        _seed_default_cards()


# === DECK OPERATIONS ===

def create_deck(
    name: str,
    short_name: str,
    black_logo_path: Optional[str] = None,
    white_logo_path: Optional[str] = None
) -> int:
    """Create a new deck and return its ID."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO decks (name, short_name, black_logo_path, white_logo_path)
            VALUES (?, ?, ?, ?)
        """, (name, short_name[:5].upper(), black_logo_path, white_logo_path))
        return cursor.lastrowid


def get_deck(deck_id: int) -> Optional[Deck]:
    """Get a deck by ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        row = cursor.fetchone()

        if not row:
            return None

        config = DeckConfig(
            name=row["name"],
            short_name=row["short_name"],
            black_logo_path=row["black_logo_path"],
            white_logo_path=row["white_logo_path"],
            primary_color=row["primary_color"],
            secondary_color=row["secondary_color"]
        )

        deck = Deck(config=config)
        deck.id = row["id"]

        # Load cards
        cursor.execute("""
            SELECT * FROM cards WHERE deck_id = ? ORDER BY id
        """, (deck_id,))

        for card_row in cursor.fetchall():
            card = Card(
                text=card_row["text"],
                card_type=CardType(card_row["card_type"]),
                pick=card_row["pick"]
            )
            card.id = card_row["id"]

            if card.card_type == CardType.BLACK:
                deck.black_cards.append(card)
            else:
                deck.white_cards.append(card)

        return deck


def list_decks() -> list[dict]:
    """List all decks."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.name, d.short_name,
                   COUNT(CASE WHEN c.card_type = 'black' THEN 1 END) as black_count,
                   COUNT(CASE WHEN c.card_type = 'white' THEN 1 END) as white_count
            FROM decks d
            LEFT JOIN cards c ON d.id = c.deck_id
            GROUP BY d.id
            ORDER BY d.updated_at DESC
        """)

        return [dict(row) for row in cursor.fetchall()]


def update_deck(
    deck_id: int,
    name: str,
    short_name: str,
    black_logo_path: Optional[str] = None,
    white_logo_path: Optional[str] = None
):
    """Update a deck."""
    with db_cursor() as cursor:
        cursor.execute("""
            UPDATE decks
            SET name = ?, short_name = ?, black_logo_path = ?, white_logo_path = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, short_name[:5].upper(), black_logo_path, white_logo_path, deck_id))


def delete_deck(deck_id: int):
    """Delete a deck and all its cards."""
    with db_cursor() as cursor:
        cursor.execute("DELETE FROM decks WHERE id = ?", (deck_id,))


def duplicate_deck(deck_id: int, new_name: str) -> int:
    """Duplicate a deck with a new name."""
    deck = get_deck(deck_id)
    if not deck:
        raise ValueError(f"Deck {deck_id} not found")

    new_deck_id = create_deck(
        new_name,
        deck.config.short_name,
        deck.config.black_logo_path,
        deck.config.white_logo_path
    )

    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO cards (deck_id, text, card_type, pick)
            SELECT ?, text, card_type, pick FROM cards WHERE deck_id = ?
        """, (new_deck_id, deck_id))

    return new_deck_id


# === CARD OPERATIONS ===

def add_card(deck_id: int, text: str, card_type: CardType, pick: int = 1) -> int:
    """Add a card to a deck and return its ID."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO cards (deck_id, text, card_type, pick)
            VALUES (?, ?, ?, ?)
        """, (deck_id, text, card_type.value, pick))

        # Update deck timestamp
        cursor.execute("""
            UPDATE decks SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (deck_id,))

        return cursor.lastrowid


def update_card(card_id: int, text: str, pick: int = 1):
    """Update a card."""
    with db_cursor() as cursor:
        cursor.execute("""
            UPDATE cards SET text = ?, pick = ? WHERE id = ?
        """, (text, pick, card_id))

        # Update deck timestamp
        cursor.execute("""
            UPDATE decks SET updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT deck_id FROM cards WHERE id = ?)
        """, (card_id,))


def delete_card(card_id: int):
    """Delete a card."""
    with db_cursor() as cursor:
        # Update deck timestamp before deleting
        cursor.execute("""
            UPDATE decks SET updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT deck_id FROM cards WHERE id = ?)
        """, (card_id,))

        cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))


def get_card(card_id: int) -> Optional[Card]:
    """Get a card by ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()

        if not row:
            return None

        card = Card(
            text=row["text"],
            card_type=CardType(row["card_type"]),
            pick=row["pick"]
        )
        card.id = row["id"]
        return card


def search_cards(deck_id: int, query: str, card_type: Optional[str] = None) -> list[Card]:
    """Search cards in a deck."""
    with db_cursor() as cursor:
        sql = "SELECT * FROM cards WHERE deck_id = ? AND text LIKE ?"
        params = [deck_id, f"%{query}%"]

        if card_type:
            sql += " AND card_type = ?"
            params.append(card_type)

        sql += " ORDER BY id"
        cursor.execute(sql, params)

        cards = []
        for row in cursor.fetchall():
            card = Card(
                text=row["text"],
                card_type=CardType(row["card_type"]),
                pick=row["pick"]
            )
            card.id = row["id"]
            cards.append(card)

        return cards


# === UTILITIES ===

def get_default_deck_id() -> Optional[int]:
    """Get the default deck ID."""
    with db_cursor() as cursor:
        # First check if a default deck is set
        cursor.execute("SELECT value FROM settings WHERE key = 'default_deck_id'")
        row = cursor.fetchone()
        if row and row["value"]:
            deck_id = int(row["value"])
            # Verify deck still exists
            cursor.execute("SELECT id FROM decks WHERE id = ?", (deck_id,))
            if cursor.fetchone():
                return deck_id

        # Fallback: return first deck
        cursor.execute("SELECT id FROM decks ORDER BY id LIMIT 1")
        row = cursor.fetchone()
        return row["id"] if row else None


def set_default_deck_id(deck_id: int):
    """Set the default deck."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES ('default_deck_id', ?)
        """, (str(deck_id),))


def get_stats() -> dict:
    """Get global statistics."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(DISTINCT d.id) as deck_count,
                COUNT(CASE WHEN c.card_type = 'black' THEN 1 END) as black_count,
                COUNT(CASE WHEN c.card_type = 'white' THEN 1 END) as white_count
            FROM decks d
            LEFT JOIN cards c ON d.id = c.deck_id
        """)
        row = cursor.fetchone()
        return dict(row)
