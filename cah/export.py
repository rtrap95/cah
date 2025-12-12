"""Export delle carte in PDF."""

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


# Dimensioni carta (stile carte da gioco)
CARD_WIDTH = 63 * mm
CARD_HEIGHT = 88 * mm
CARD_MARGIN = 5 * mm
CARD_PADDING = 4 * mm
CORNER_RADIUS = 3 * mm

# Layout pagina
PAGE_MARGIN = 10 * mm
CARDS_PER_ROW = 3
CARDS_PER_COL = 3
CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL


def hex_to_rgb(hex_color: str) -> tuple:
    """Converte colore hex in RGB normalizzato (0-1)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b)


def draw_rounded_rect(c: canvas.Canvas, x: float, y: float,
                      width: float, height: float, radius: float,
                      fill_color: tuple, stroke_color: tuple = None):
    """Disegna un rettangolo con angoli arrotondati."""
    c.setFillColorRGB(*fill_color)
    if stroke_color:
        c.setStrokeColorRGB(*stroke_color)
        c.setLineWidth(0.5)
    else:
        c.setStrokeColorRGB(*fill_color)

    # Usa roundRect di reportlab per un rettangolo corretto
    c.roundRect(x, y, width, height, radius,
                fill=1, stroke=1 if stroke_color else 0)


def wrap_text(text: str, max_chars: int = 25) -> list[str]:
    """Divide il testo in righe."""
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
              deck_name: str, short_name: str, logo_path: str | None = None):
    """Disegna una singola carta."""
    # Colori basati sul tipo
    if card.card_type == CardType.BLACK:
        bg_color = (0, 0, 0)
        text_color = (1, 1, 1)
    else:
        bg_color = (1, 1, 1)
        text_color = (0, 0, 0)

    # Sfondo carta
    draw_rounded_rect(c, x, y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS,
                      bg_color, (0.5, 0.5, 0.5))

    # Logo o nome breve in alto a sinistra
    c.setFillColorRGB(*text_color)

    if logo_path and Path(logo_path).exists():
        try:
            logo_size = 10 * mm
            img = Image.open(logo_path)
            # Inverti colori per carte nere se necessario
            c.drawImage(ImageReader(img),
                       x + CARD_PADDING,
                       y + CARD_HEIGHT - CARD_PADDING - logo_size,
                       width=logo_size, height=logo_size,
                       preserveAspectRatio=True, mask='auto')
        except Exception:
            # Fallback al nome breve
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + CARD_PADDING, y + CARD_HEIGHT - CARD_PADDING - 8, short_name)
    else:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + CARD_PADDING, y + CARD_HEIGHT - CARD_PADDING - 8, short_name)

    # Testo carta
    text_lines = wrap_text(card.text, 22)
    font_size = 11 if len(text_lines) <= 4 else 9
    c.setFont("Helvetica-Bold", font_size)

    text_start_y = y + CARD_HEIGHT - 25 * mm
    line_height = font_size + 3

    for i, line in enumerate(text_lines):
        c.drawString(x + CARD_PADDING, text_start_y - (i * line_height), line)

    # Nome mazzo in basso
    c.setFont("Helvetica", 6)
    c.drawString(x + CARD_PADDING, y + CARD_PADDING, deck_name)

    # Indicatore "Pick X" per carte nere con pick > 1
    if card.card_type == CardType.BLACK and card.pick > 1:
        c.setFont("Helvetica-Bold", 8)
        pick_text = f"PESCA {card.pick}"
        c.drawRightString(x + CARD_WIDTH - CARD_PADDING, y + CARD_PADDING, pick_text)


def export_deck_to_pdf(deck: Deck, output_path: Path,
                       cards_type: str = "all") -> Path:
    """Esporta un mazzo in PDF.

    Args:
        deck: Il mazzo da esportare
        output_path: Percorso del file PDF
        cards_type: "all", "black", o "white"

    Returns:
        Percorso del file creato
    """
    c = canvas.Canvas(str(output_path), pagesize=A4)
    page_width, page_height = A4

    # Seleziona le carte da esportare
    cards_to_export = []
    if cards_type in ("all", "black"):
        cards_to_export.extend(deck.black_cards)
    if cards_type in ("all", "white"):
        cards_to_export.extend(deck.white_cards)

    if not cards_to_export:
        raise ValueError("Nessuna carta da esportare")

    deck_name = deck.config.name
    short_name = deck.config.short_name
    logo_path = deck.config.logo_path

    # Calcola posizione iniziale
    start_x = (page_width - (CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_MARGIN)) / 2
    start_y = page_height - PAGE_MARGIN - CARD_HEIGHT

    for i, card in enumerate(cards_to_export):
        # Nuova pagina se necessario
        if i > 0 and i % CARDS_PER_PAGE == 0:
            c.showPage()

        # Calcola posizione sulla pagina
        page_index = i % CARDS_PER_PAGE
        col = page_index % CARDS_PER_ROW
        row = page_index // CARDS_PER_ROW

        x = start_x + col * (CARD_WIDTH + CARD_MARGIN)
        y = start_y - row * (CARD_HEIGHT + CARD_MARGIN)

        draw_card(c, card, x, y, deck_name, short_name, logo_path)

    c.save()
    return output_path


def export_cards_preview(cards: list[Card], output_path: Path,
                         deck_name: str = "Cards Against Humanity",
                         short_name: str = "CAH") -> Path:
    """Esporta un'anteprima di carte selezionate."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    page_width, page_height = A4

    start_x = (page_width - (CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_MARGIN)) / 2
    start_y = page_height - PAGE_MARGIN - CARD_HEIGHT

    for i, card in enumerate(cards[:CARDS_PER_PAGE]):
        col = i % CARDS_PER_ROW
        row = i // CARDS_PER_ROW

        x = start_x + col * (CARD_WIDTH + CARD_MARGIN)
        y = start_y - row * (CARD_HEIGHT + CARD_MARGIN)

        draw_card(c, card, x, y, deck_name, short_name, None)

    c.save()
    return output_path
