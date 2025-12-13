"""Export cards to PDF."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image

from .models import Card, CardType, Deck


# Card dimensions (playing card style)
CARD_WIDTH = 58 * mm
CARD_HEIGHT = 88 * mm
CARD_MARGIN = 5 * mm
CARD_PADDING = 4 * mm
CORNER_RADIUS = 3 * mm

# Page layout
PAGE_MARGIN = 10 * mm
CARDS_PER_ROW = 3
CARDS_PER_COL = 3
CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to normalized RGB (0-1)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b)


def draw_rounded_rect(c: canvas.Canvas, x: float, y: float,
                      width: float, height: float, radius: float,
                      fill_color: tuple, stroke_color: tuple = None):
    """Draw a rectangle with rounded corners."""
    c.setFillColorRGB(*fill_color)
    if stroke_color:
        c.setStrokeColorRGB(*stroke_color)
        c.setLineWidth(0.5)
    else:
        c.setStrokeColorRGB(*fill_color)

    # Use reportlab's roundRect for correct rectangle
    c.roundRect(x, y, width, height, radius,
                fill=1, stroke=1 if stroke_color else 0)


def wrap_text(text: str, max_chars: int = 25) -> list[str]:
    """Split text into lines."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line = f"{current_line} {word}".strip()
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def draw_card(c: canvas.Canvas, card: Card, x: float, y: float,
              deck_name: str, short_name: str,
              black_logo_path: str | None = None,
              white_logo_path: str | None = None):
    """Draw a single card."""
    # Colors based on type
    if card.card_type == CardType.BLACK:
        bg_color = (0, 0, 0)
        text_color = (1, 1, 1)
        logo_path = black_logo_path
    else:
        bg_color = (1, 1, 1)
        text_color = (0, 0, 0)
        logo_path = white_logo_path

    # Card background
    draw_rounded_rect(c, x, y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS,
                      bg_color, (0.5, 0.5, 0.5))

    c.setFillColorRGB(*text_color)

    # Deck name at top, centered
    c.setFont("Helvetica-Bold", 7)
    deck_name_width = c.stringWidth(deck_name, "Helvetica-Bold", 7)
    c.drawString(x + (CARD_WIDTH - deck_name_width) / 2, y + CARD_HEIGHT - CARD_PADDING - 7, deck_name)

    # Card text
    text_lines = wrap_text(card.text, 22)
    font_size = 11 if len(text_lines) <= 4 else 9
    c.setFont("Helvetica-Bold", font_size)

    text_start_y = y + CARD_HEIGHT - 20 * mm
    line_height = font_size + 3

    for i, line in enumerate(text_lines):
        c.drawString(x + CARD_PADDING, text_start_y - (i * line_height), line)

    # Logo or short name in bottom right
    logo_size = 15 * mm
    if logo_path and Path(logo_path).exists():
        try:
            img = Image.open(logo_path)
            c.drawImage(ImageReader(img),
                       x + CARD_WIDTH - CARD_PADDING - logo_size,
                       y + CARD_PADDING,
                       width=logo_size, height=logo_size,
                       preserveAspectRatio=True, mask='auto')
        except Exception:
            # Fallback to short name
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(x + CARD_WIDTH - CARD_PADDING, y + CARD_PADDING, short_name)
    else:
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x + CARD_WIDTH - CARD_PADDING, y + CARD_PADDING, short_name)

    # "Pick X" indicator for black cards with pick > 1 (bottom left)
    if card.card_type == CardType.BLACK and card.pick > 1:
        c.setFont("Helvetica-Bold", 8)
        pick_text = f"PICK {card.pick}"
        c.drawString(x + CARD_PADDING, y + CARD_PADDING, pick_text)


def export_deck_to_pdf(deck: Deck, output_path: Path,
                       cards_type: str = "all") -> Path:
    """Export a deck to PDF.

    Args:
        deck: The deck to export
        output_path: PDF file path
        cards_type: "all", "black", or "white"

    Returns:
        Path of created file
    """
    c = canvas.Canvas(str(output_path), pagesize=A4)
    page_width, page_height = A4

    # Select cards to export
    cards_to_export = []
    if cards_type in ("all", "black"):
        cards_to_export.extend(deck.black_cards)
    if cards_type in ("all", "white"):
        cards_to_export.extend(deck.white_cards)

    if not cards_to_export:
        raise ValueError("No cards to export")

    deck_name = deck.config.name
    short_name = deck.config.short_name
    black_logo_path = deck.config.black_logo_path
    white_logo_path = deck.config.white_logo_path

    # Calculate starting position
    start_x = (page_width - (CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_MARGIN)) / 2
    start_y = page_height - PAGE_MARGIN - CARD_HEIGHT

    for i, card in enumerate(cards_to_export):
        # New page if needed
        if i > 0 and i % CARDS_PER_PAGE == 0:
            c.showPage()

        # Calculate position on page
        page_index = i % CARDS_PER_PAGE
        col = page_index % CARDS_PER_ROW
        row = page_index // CARDS_PER_ROW

        x = start_x + col * (CARD_WIDTH + CARD_MARGIN)
        y = start_y - row * (CARD_HEIGHT + CARD_MARGIN)

        draw_card(c, card, x, y, deck_name, short_name, black_logo_path, white_logo_path)

    c.save()
    return output_path


def export_cards_preview(cards: list[Card], output_path: Path,
                         deck_name: str = "Cards Against Humanity",
                         short_name: str = "CAH",
                         black_logo_path: str | None = None,
                         white_logo_path: str | None = None) -> Path:
    """Export a preview of selected cards."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    page_width, page_height = A4

    start_x = (page_width - (CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_MARGIN)) / 2
    start_y = page_height - PAGE_MARGIN - CARD_HEIGHT

    for i, card in enumerate(cards[:CARDS_PER_PAGE]):
        col = i % CARDS_PER_ROW
        row = i // CARDS_PER_ROW

        x = start_x + col * (CARD_WIDTH + CARD_MARGIN)
        y = start_y - row * (CARD_HEIGHT + CARD_MARGIN)

        draw_card(c, card, x, y, deck_name, short_name, black_logo_path, white_logo_path)

    c.save()
    return output_path
