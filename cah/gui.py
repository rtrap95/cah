"""GUI for the Cards Against Humanity generator."""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import random
import subprocess
import platform

from .models import CardType, DeckConfig, Card, Deck
from . import db
from .export import export_deck_to_pdf

# Theme configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


class CardFrame(ctk.CTkFrame):
    """Frame representing a clickable card."""

    def __init__(self, master, card: Card, on_click=None, index=None, **kwargs):
        is_black = card.card_type == CardType.BLACK
        fg_color = "#1a1a1a" if is_black else "#f5f5f5"
        hover_color = "#333333" if is_black else "#e0e0e0"
        super().__init__(master, fg_color=fg_color, corner_radius=10, **kwargs)

        self.card = card
        self.on_click = on_click
        self.default_color = fg_color
        self.hover_color = hover_color
        text_color = "white" if is_black else "black"
        index_color = "#666666" if is_black else "#999999"

        # Header with index
        if index is not None:
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(8, 0))

            self.index_label = ctk.CTkLabel(
                header,
                text=f"#{index}",
                text_color=index_color,
                font=ctk.CTkFont(size=10)
            )
            self.index_label.pack(side="left")

        self.label = ctk.CTkLabel(
            self,
            text=card.text,
            text_color=text_color,
            font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=180,
            justify="left"
        )
        self.label.pack(padx=15, pady=(5 if index else 15, 15), fill="both", expand=True)

        # Bind click events
        if on_click:
            self.bind("<Button-1>", self._handle_click)
            self.label.bind("<Button-1>", self._handle_click)
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.label.configure(cursor="hand2")
            self.configure(cursor="hand2")

    def _handle_click(self, event):
        if self.on_click:
            self.on_click(self.card)

    def _on_enter(self, event):
        self.configure(fg_color=self.hover_color)

    def _on_leave(self, event):
        self.configure(fg_color=self.default_color)


class CAHApp(ctk.CTk):
    """Main application."""

    def __init__(self):
        super().__init__()

        self.title("Cards Against Humanity - Generator")
        self.geometry("1200x800")
        self.minsize(900, 650)

        # Initialize database
        db.ensure_db()

        # Load default deck or first available
        deck_id = db.get_default_deck_id()
        if deck_id:
            self.current_deck = db.get_deck(deck_id)
        else:
            # Create empty deck if none exists
            deck_id = db.create_deck("Cards Against Humanity", "CAH")
            self.current_deck = db.get_deck(deck_id)

        # Pagination
        self._page = 0
        self._cards_per_page = 30

        self._create_layout()
        self._refresh_cards_view()

    def _create_layout(self):
        """Create the main layout."""
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="CAH",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.logo_label.pack(pady=(20, 5))

        self.subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Generator",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle.pack(pady=(0, 20))

        # Statistics
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=10, pady=5)

        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.stats_label.pack()

        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=20)

        self.btn_black = ctk.CTkButton(
            self.nav_frame,
            text="Black Cards",
            command=lambda: self._show_cards("black"),
            fg_color="#333333",
            hover_color="#444444"
        )
        self.btn_black.pack(fill="x", pady=5)

        self.btn_white = ctk.CTkButton(
            self.nav_frame,
            text="White Cards",
            command=lambda: self._show_cards("white"),
            fg_color="#e0e0e0",
            text_color="black",
            hover_color="#d0d0d0"
        )
        self.btn_white.pack(fill="x", pady=5)

        self.btn_random = ctk.CTkButton(
            self.nav_frame,
            text="Random Combo",
            command=self._show_random_combo,
            fg_color="#c0392b",
            hover_color="#a93226"
        )
        self.btn_random.pack(fill="x", pady=5)

        # Separator
        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=15)

        # Deck management
        self.deck_label = ctk.CTkLabel(
            self.sidebar,
            text="Decks",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.deck_label.pack(pady=(5, 10))

        self.btn_new_deck = ctk.CTkButton(
            self.sidebar,
            text="+ New Deck",
            command=self._create_new_deck,
            width=160
        )
        self.btn_new_deck.pack(pady=5)

        self.btn_load_deck = ctk.CTkButton(
            self.sidebar,
            text="Load Deck",
            command=self._load_deck_dialog,
            width=160,
            fg_color="transparent",
            border_width=1
        )
        self.btn_load_deck.pack(pady=5)

        self.btn_set_default = ctk.CTkButton(
            self.sidebar,
            text="Set as Default",
            command=self._set_as_default,
            width=160,
            fg_color="transparent",
            border_width=1,
            text_color="gray"
        )
        self.btn_set_default.pack(pady=5)

        self.btn_add_card = ctk.CTkButton(
            self.sidebar,
            text="+ Add Card",
            command=self._add_card_dialog,
            width=160,
            fg_color="#27ae60",
            hover_color="#219a52"
        )
        self.btn_add_card.pack(pady=5)

        self.btn_add_batch = ctk.CTkButton(
            self.sidebar,
            text="+ Add Multiple",
            command=self._add_batch_dialog,
            width=160,
            fg_color="#2980b9",
            hover_color="#2472a4"
        )
        self.btn_add_batch.pack(pady=5)

        # Export at bottom
        self.btn_copy_text = ctk.CTkButton(
            self.sidebar,
            text="Copy as Text",
            command=self._copy_as_text,
            width=160,
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        self.btn_copy_text.pack(side="bottom", pady=(0, 10))

        self.btn_export = ctk.CTkButton(
            self.sidebar,
            text="Export PDF",
            command=self._export_pdf,
            width=160,
            height=40,
            fg_color="#8e44ad",
            hover_color="#7d3c98"
        )
        self.btn_export.pack(side="bottom", pady=(0, 10))

        # Main area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Main area header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="All Cards",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left")

        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_cards())

        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Search...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="right")

        # Scrollable card area
        self.cards_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.cards_scroll.pack(fill="both", expand=True)

        # Pagination at bottom
        self.pagination_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pagination_frame.pack(fill="x", pady=(10, 0))

        self.btn_prev_page = ctk.CTkButton(
            self.pagination_frame,
            text="← Previous",
            command=self._prev_page,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.btn_prev_page.pack(side="left")

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1/1",
            font=ctk.CTkFont(size=12)
        )
        self.page_label.pack(side="left", expand=True)

        self.btn_next_page = ctk.CTkButton(
            self.pagination_frame,
            text="Next →",
            command=self._next_page,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.btn_next_page.pack(side="right")

        # Mouse scroll fix for macOS
        self._setup_mousewheel_scroll()

    def _setup_mousewheel_scroll(self):
        """Configure mouse/trackpad and keyboard scroll."""
        canvas = self.cards_scroll._parent_canvas
        self._scroll_canvas = canvas

        # Keyboard scroll (always works)
        self.bind_all("<Up>", lambda e: canvas.yview_scroll(-3, "units"))
        self.bind_all("<Down>", lambda e: canvas.yview_scroll(3, "units"))
        self.bind_all("<Prior>", lambda e: canvas.yview_scroll(-10, "units"))  # Page Up
        self.bind_all("<Next>", lambda e: canvas.yview_scroll(10, "units"))    # Page Down
        self.bind_all("<Home>", lambda e: canvas.yview_moveto(0))
        self.bind_all("<End>", lambda e: canvas.yview_moveto(1))

        # Page change with left/right arrows (not in text fields)
        self.bind_all("<Left>", self._on_left_key)
        self.bind_all("<Right>", self._on_right_key)

        # Mouse wheel - use Enter/Leave to bind/unbind
        self.cards_scroll.bind("<Enter>", self._on_enter_scroll_area)
        self.cards_scroll.bind("<Leave>", self._on_leave_scroll_area)

    def _on_enter_scroll_area(self, event):
        """Enable scroll when mouse enters the area."""
        if platform.system() == "Darwin":
            self.bind_all("<MouseWheel>", self._on_mousewheel_mac)
        else:
            self.bind_all("<MouseWheel>", self._on_mousewheel_other)
            self.bind_all("<Button-4>", self._on_scroll_up)
            self.bind_all("<Button-5>", self._on_scroll_down)

    def _on_leave_scroll_area(self, event):
        """Disable scroll when mouse leaves the area."""
        self.unbind_all("<MouseWheel>")
        if platform.system() != "Darwin":
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")

    def _on_mousewheel_mac(self, event):
        """Scroll on macOS."""
        self._scroll_canvas.yview_scroll(-event.delta, "units")

    def _on_mousewheel_other(self, event):
        """Scroll on Windows/Linux."""
        self._scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _on_scroll_up(self, event):
        self._scroll_canvas.yview_scroll(-3, "units")

    def _on_scroll_down(self, event):
        self._scroll_canvas.yview_scroll(3, "units")

    def _on_left_key(self, event):
        """Previous page if not in text field."""
        if not isinstance(event.widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            self._prev_page()

    def _on_right_key(self, event):
        """Next page if not in text field."""
        if not isinstance(event.widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            self._next_page()

    def _refresh_cards_view(self, card_type: str = "all", reset_page: bool = True):
        """Refresh the cards display."""
        # Save current type for subsequent refreshes
        self._current_view_type = card_type

        # Reset page when view or search changes
        if reset_page:
            self._page = 0

        # Clear
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        # Select cards
        if card_type == "black":
            all_cards = self.current_deck.black_cards
            self.title_label.configure(text="Black Cards (Questions)")
        elif card_type == "white":
            all_cards = self.current_deck.white_cards
            self.title_label.configure(text="White Cards (Answers)")
        else:
            all_cards = self.current_deck.black_cards + self.current_deck.white_cards
            self.title_label.configure(text="All Cards")

        # Filter by search
        search_term = self.search_var.get().lower()
        if search_term:
            all_cards = [c for c in all_cards if search_term in c.text.lower()]

        # Calculate pagination
        total_cards = len(all_cards)
        total_pages = max(1, (total_cards + self._cards_per_page - 1) // self._cards_per_page)
        self._page = min(self._page, total_pages - 1)

        start_idx = self._page * self._cards_per_page
        end_idx = min(start_idx + self._cards_per_page, total_cards)
        cards = all_cards[start_idx:end_idx]

        # Update pagination UI
        self.page_label.configure(text=f"Page {self._page + 1}/{total_pages} ({total_cards} cards)")
        self.btn_prev_page.configure(state="normal" if self._page > 0 else "disabled")
        self.btn_next_page.configure(state="normal" if self._page < total_pages - 1 else "disabled")

        # Calculate base indices for this page
        # Count how many black/white cards before this page
        black_before = sum(1 for c in all_cards[:start_idx] if c.card_type == CardType.BLACK)
        white_before = sum(1 for c in all_cards[:start_idx] if c.card_type == CardType.WHITE)

        # Card grid
        cols = 3
        black_idx = black_before
        white_idx = white_before
        for i, card in enumerate(cards):
            row = i // cols
            col = i % cols

            # Separate index for black and white
            if card.card_type == CardType.BLACK:
                black_idx += 1
                display_idx = black_idx
            else:
                white_idx += 1
                display_idx = white_idx

            card_frame = CardFrame(self.cards_scroll, card, on_click=self._edit_card, index=display_idx)
            card_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Configure grid
        for i in range(cols):
            self.cards_scroll.columnconfigure(i, weight=1)

        # Scroll to top
        self.cards_scroll._parent_canvas.yview_moveto(0)

    def _show_cards(self, card_type: str):
        """Show cards of a specific type."""
        self._refresh_cards_view(card_type)

    def _prev_page(self):
        """Go to previous page."""
        if self._page > 0:
            self._page -= 1
            current_type = getattr(self, '_current_view_type', 'all')
            self._refresh_cards_view(current_type, reset_page=False)

    def _next_page(self):
        """Go to next page."""
        self._page += 1
        current_type = getattr(self, '_current_view_type', 'all')
        self._refresh_cards_view(current_type, reset_page=False)

    def _filter_cards(self):
        """Filter cards based on search."""
        current_type = getattr(self, '_current_view_type', 'all')
        self._refresh_cards_view(current_type)  # reset_page=True by default

    def _edit_card(self, card: Card):
        """Open dialog to edit a card."""
        dialog = EditCardDialog(self, card)
        self.wait_window(dialog)

        if dialog.result:
            action, new_text, new_pick = dialog.result

            if action == "delete":
                # Remove card from database
                if card.id:
                    db.delete_card(card.id)
                # Remove from local list
                if card.card_type == CardType.BLACK:
                    self.current_deck.black_cards.remove(card)
                else:
                    self.current_deck.white_cards.remove(card)
            elif action == "save":
                # Update card in database
                if card.id:
                    db.update_card(card.id, new_text, new_pick)
                # Update locally
                card.text = new_text
                card.pick = new_pick

            self._update_stats()
            current_type = getattr(self, '_current_view_type', 'all')
            self._refresh_cards_view(current_type)

    def _show_random_combo(self):
        """Show a random combination."""
        # Clear
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        self.title_label.configure(text="Random Combination")

        if not self.current_deck.black_cards or not self.current_deck.white_cards:
            ctk.CTkLabel(
                self.cards_scroll,
                text="Need black and white cards to generate combinations",
                text_color="gray"
            ).pack(pady=50)
            return

        black_card = random.choice(self.current_deck.black_cards)
        white_cards = random.sample(
            self.current_deck.white_cards,
            min(black_card.pick, len(self.current_deck.white_cards))
        )

        # Center container
        combo_frame = ctk.CTkFrame(self.cards_scroll, fg_color="transparent")
        combo_frame.pack(expand=True, pady=50)

        # Black card
        black_frame = CardFrame(combo_frame, black_card, width=250, height=150)
        black_frame.pack(pady=10)

        # Pick indicator if > 1
        if black_card.pick > 1:
            pick_label = ctk.CTkLabel(
                combo_frame,
                text=f"Pick {black_card.pick} cards",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            pick_label.pack()

        # Arrow
        arrow = ctk.CTkLabel(combo_frame, text="↓", font=ctk.CTkFont(size=30))
        arrow.pack(pady=5)

        # White cards (numbered if more than one)
        for i, wc in enumerate(white_cards, 1):
            card_container = ctk.CTkFrame(combo_frame, fg_color="transparent")
            card_container.pack(pady=3)

            if len(white_cards) > 1:
                num_label = ctk.CTkLabel(
                    card_container,
                    text=f"#{i}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#3498db",
                    width=30
                )
                num_label.pack(side="left", padx=(0, 5))

            white_frame = CardFrame(card_container, wc, width=220, height=80)
            white_frame.pack(side="left")

        # Result - build the phrase
        result = black_card.text
        blanks_count = result.count("_____")

        if blanks_count >= len(white_cards):
            # Replace blanks with cards
            for wc in white_cards:
                result = result.replace("_____", f"[{wc.text}]", 1)
        else:
            # Not enough blanks, add answers at the end
            for i, wc in enumerate(white_cards):
                if "_____" in result:
                    result = result.replace("_____", f"[{wc.text}]", 1)
                else:
                    result += f" [{wc.text}]"

        result_label = ctk.CTkLabel(
            combo_frame,
            text=result,
            font=ctk.CTkFont(size=14, slant="italic"),
            wraplength=400,
            text_color="#e74c3c"
        )
        result_label.pack(pady=20)

        # Refresh button
        btn_refresh = ctk.CTkButton(
            combo_frame,
            text="Another combination",
            command=self._show_random_combo,
            fg_color="#c0392b"
        )
        btn_refresh.pack(pady=10)

    def _create_new_deck(self):
        """Open dialog to create new deck."""
        dialog = NewDeckDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            name, short_name, black_logo, white_logo, import_default = dialog.result
            # Create deck in database
            deck_id = db.create_deck(name, short_name, black_logo, white_logo)

            if import_default:
                # Copy cards from default deck
                default_id = db.get_default_deck_id()
                if default_id and default_id != deck_id:
                    default_deck = db.get_deck(default_id)
                    for card in default_deck.black_cards + default_deck.white_cards:
                        db.add_card(deck_id, card.text, card.card_type, card.pick)

            self.current_deck = db.get_deck(deck_id)
            self._update_stats()
            self._refresh_cards_view()
            messagebox.showinfo("Success", f"Deck '{name}' created!")

    def _set_as_default(self):
        """Set current deck as default on startup."""
        if self.current_deck and self.current_deck.id:
            db.set_default_deck_id(self.current_deck.id)
            messagebox.showinfo(
                "Default",
                f"'{self.current_deck.config.name}' will be loaded on startup."
            )

    def _load_deck_dialog(self):
        """Open dialog to load a deck."""
        decks = db.list_decks()

        if not decks:
            messagebox.showinfo("Info", "No saved decks.")
            return

        dialog = LoadDeckDialog(self, decks)
        self.wait_window(dialog)

        if dialog.result:
            deck_id = dialog.result
            self.current_deck = db.get_deck(deck_id)
            self._update_stats()
            self._refresh_cards_view()

    def _add_card_dialog(self):
        """Open dialog to add a card."""
        dialog = AddCardDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            card_type, text, pick = dialog.result
            # Save to database
            card_id = db.add_card(self.current_deck.id, text, card_type, pick)
            # Add locally
            card = Card(text=text, card_type=card_type, pick=pick, id=card_id)
            if card_type == CardType.BLACK:
                self.current_deck.black_cards.append(card)
            else:
                self.current_deck.white_cards.append(card)
            self._update_stats()
            self._refresh_cards_view()
            messagebox.showinfo("Success", "Card added!")

    def _add_batch_dialog(self):
        """Open dialog to add multiple cards."""
        dialog = BatchAddDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            black_cards, white_cards = dialog.result
            count = 0

            for text in black_cards:
                if text.strip():
                    card_id = db.add_card(self.current_deck.id, text.strip(), CardType.BLACK, 1)
                    card = Card(text=text.strip(), card_type=CardType.BLACK, pick=1, id=card_id)
                    self.current_deck.black_cards.append(card)
                    count += 1

            for text in white_cards:
                if text.strip():
                    card_id = db.add_card(self.current_deck.id, text.strip(), CardType.WHITE, 1)
                    card = Card(text=text.strip(), card_type=CardType.WHITE, pick=1, id=card_id)
                    self.current_deck.white_cards.append(card)
                    count += 1

            if count > 0:
                self._update_stats()
                self._refresh_cards_view()
                messagebox.showinfo("Success", f"{count} cards added!")

    def _update_stats(self):
        """Update displayed statistics."""
        self.stats_label.configure(
            text=f"Cards: {len(self.current_deck.black_cards)} black, "
                 f"{len(self.current_deck.white_cards)} white"
        )

    def _export_pdf(self):
        """Export deck to PDF."""
        dialog = ExportDialog(self, self.current_deck)
        self.wait_window(dialog)

    def _copy_as_text(self):
        """Copy deck as text to clipboard."""
        lines = []
        lines.append(f"# {self.current_deck.config.name}")
        lines.append(f"# Black cards: {len(self.current_deck.black_cards)}, White cards: {len(self.current_deck.white_cards)}")
        lines.append("")

        lines.append("## BLACK CARDS (Questions)")
        lines.append("")
        for i, card in enumerate(self.current_deck.black_cards, 1):
            pick_info = f" [PICK {card.pick}]" if card.pick > 1 else ""
            lines.append(f"{i}. {card.text}{pick_info}")

        lines.append("")
        lines.append("## WHITE CARDS (Answers)")
        lines.append("")
        for i, card in enumerate(self.current_deck.white_cards, 1):
            lines.append(f"{i}. {card.text}")

        text = "\n".join(lines)

        # Copy to clipboard
        self.clipboard_clear()
        self.clipboard_append(text)

        messagebox.showinfo(
            "Copied!",
            f"Deck copied to clipboard!\n\n"
            f"{len(self.current_deck.black_cards)} black cards\n"
            f"{len(self.current_deck.white_cards)} white cards"
        )


class NewDeckDialog(ctk.CTkToplevel):
    """Dialog to create a new deck."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("New Deck")
        self.geometry("400x480")
        self.resizable(False, False)

        # Fields
        ctk.CTkLabel(self, text="Deck name:").pack(pady=(20, 5))
        self.name_entry = ctk.CTkEntry(self, width=300)
        self.name_entry.pack()
        self.name_entry.insert(0, "My deck")

        ctk.CTkLabel(self, text="Short name (max 5 characters):").pack(pady=(15, 5))
        self.short_entry = ctk.CTkEntry(self, width=100)
        self.short_entry.pack()
        self.short_entry.insert(0, "DECK")

        # Logo for black cards
        ctk.CTkLabel(self, text="Logo for black cards (optional):").pack(pady=(15, 5))
        self.black_logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.black_logo_frame.pack()

        self.black_logo_path = ctk.StringVar()
        self.black_logo_entry = ctk.CTkEntry(self.black_logo_frame, width=200, textvariable=self.black_logo_path)
        self.black_logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            self.black_logo_frame,
            text="Browse",
            width=80,
            command=lambda: self._browse_logo(self.black_logo_path)
        ).pack(side="left")

        # Logo for white cards
        ctk.CTkLabel(self, text="Logo for white cards (optional):").pack(pady=(10, 5))
        self.white_logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.white_logo_frame.pack()

        self.white_logo_path = ctk.StringVar()
        self.white_logo_entry = ctk.CTkEntry(self.white_logo_frame, width=200, textvariable=self.white_logo_path)
        self.white_logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            self.white_logo_frame,
            text="Browse",
            width=80,
            command=lambda: self._browse_logo(self.white_logo_path)
        ).pack(side="left")

        # Import default cards checkbox
        self.import_default = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self,
            text="Import default cards",
            variable=self.import_default
        ).pack(pady=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Create", command=self._create).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _browse_logo(self, var: ctk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        if path:
            var.set(path)

    def _create(self):
        name = self.name_entry.get().strip() or "My deck"
        short_name = self.short_entry.get().strip()[:5].upper() or "DECK"
        black_logo = self.black_logo_path.get() or None
        white_logo = self.white_logo_path.get() or None

        # Return parameters instead of creating deck
        self.result = (name, short_name, black_logo, white_logo, self.import_default.get())
        self.destroy()


class LoadDeckDialog(ctk.CTkToplevel):
    """Dialog to load a saved deck."""

    def __init__(self, parent, decks: list):
        super().__init__(parent)
        self.result = None
        self.decks = decks

        self.title("Load Deck")
        self.geometry("400x380")
        self.resizable(False, False)

        ctk.CTkLabel(
            self,
            text="Select a deck:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=20)

        # Deck list
        self.listbox_frame = ctk.CTkScrollableFrame(self, width=350, height=150)
        self.listbox_frame.pack(pady=10)

        self.selected_idx = ctk.IntVar(value=0)

        for i, deck in enumerate(decks):
            rb = ctk.CTkRadioButton(
                self.listbox_frame,
                text=f"{deck['name']} ({deck['black_count']}B, {deck['white_count']}W)",
                variable=self.selected_idx,
                value=i
            )
            rb.pack(anchor="w", pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Load", command=self._load).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self._delete,
            fg_color="#c0392b"
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _load(self):
        idx = self.selected_idx.get()
        self.result = self.decks[idx]["id"]
        self.destroy()

    def _delete(self):
        idx = self.selected_idx.get()
        if messagebox.askyesno("Confirm", f"Delete '{self.decks[idx]['name']}'?"):
            db.delete_deck(self.decks[idx]["id"])
            self.destroy()


class AddCardDialog(ctk.CTkToplevel):
    """Dialog to add a card."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Add Card")
        self.geometry("400x380")
        self.resizable(False, False)

        # Card type
        ctk.CTkLabel(self, text="Card type:").pack(pady=(20, 5))

        self.card_type = ctk.StringVar(value="black")
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack()

        ctk.CTkRadioButton(
            type_frame,
            text="Black (question)",
            variable=self.card_type,
            value="black"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            type_frame,
            text="White (answer)",
            variable=self.card_type,
            value="white"
        ).pack(side="left", padx=10)

        # Text
        ctk.CTkLabel(self, text="Text (use _____ for blanks):").pack(pady=(15, 5))
        self.text_entry = ctk.CTkTextbox(self, width=350, height=80)
        self.text_entry.pack()

        # Pick (black cards only)
        pick_frame = ctk.CTkFrame(self, fg_color="transparent")
        pick_frame.pack(pady=10)

        ctk.CTkLabel(pick_frame, text="Cards to pick:").pack(side="left")
        self.pick_var = ctk.StringVar(value="1")
        self.pick_menu = ctk.CTkOptionMenu(
            pick_frame,
            values=["1", "2", "3"],
            variable=self.pick_var,
            width=60
        )
        self.pick_menu.pack(side="left", padx=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Add", command=self._add).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _add(self):
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter card text.")
            return

        card_type = CardType.BLACK if self.card_type.get() == "black" else CardType.WHITE
        pick = int(self.pick_var.get())

        self.result = (card_type, text, pick)
        self.destroy()


class BatchAddDialog(ctk.CTkToplevel):
    """Dialog to add multiple cards at once."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Add Multiple Cards")
        self.geometry("500x550")
        self.resizable(False, False)

        ctk.CTkLabel(
            self,
            text="Add multiple cards (one per line)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))

        # Black cards
        black_frame = ctk.CTkFrame(self)
        black_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            black_frame,
            text="Black Cards (questions):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkLabel(
            black_frame,
            text="Use _____ for blanks",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w")

        self.black_text = ctk.CTkTextbox(black_frame, width=440, height=120)
        self.black_text.pack(pady=5)
        self.black_text.insert("1.0", "What keeps me awake at night? _____.\nThe secret to happiness is _____.")

        # White cards
        white_frame = ctk.CTkFrame(self)
        white_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            white_frame,
            text="White Cards (answers):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(5, 0))

        self.white_text = ctk.CTkTextbox(white_frame, width=440, height=120)
        self.white_text.pack(pady=5)
        self.white_text.insert("1.0", "A judgmental cat\nPineapple pizza\nMonday mornings")

        # Info
        ctk.CTkLabel(
            self,
            text="Each line becomes a separate card",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="Add All",
            command=self._add,
            fg_color="#27ae60",
            hover_color="#219a52"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _add(self):
        black_lines = self.black_text.get("1.0", "end").strip().split("\n")
        white_lines = self.white_text.get("1.0", "end").strip().split("\n")

        # Filter empty lines
        black_cards = [line for line in black_lines if line.strip()]
        white_cards = [line for line in white_lines if line.strip()]

        if not black_cards and not white_cards:
            messagebox.showwarning("Warning", "Please enter at least one card.")
            return

        self.result = (black_cards, white_cards)
        self.destroy()


class EditCardDialog(ctk.CTkToplevel):
    """Dialog to edit or delete a card."""

    def __init__(self, parent, card: Card):
        super().__init__(parent)
        self.result = None
        self.card = card

        is_black = card.card_type == CardType.BLACK
        title_type = "Black" if is_black else "White"

        self.title(f"Edit {title_type} Card")
        self.geometry("450x350")
        self.resizable(False, False)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="#1a1a1a" if is_black else "#f5f5f5", corner_radius=10)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header_frame,
            text=f"{title_type} Card",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white" if is_black else "black"
        ).pack(pady=10)

        # Text
        ctk.CTkLabel(self, text="Card text:").pack(pady=(10, 5))
        self.text_entry = ctk.CTkTextbox(self, width=400, height=100)
        self.text_entry.pack()
        self.text_entry.insert("1.0", card.text)

        # Pick (black cards only)
        if is_black:
            pick_frame = ctk.CTkFrame(self, fg_color="transparent")
            pick_frame.pack(pady=10)

            ctk.CTkLabel(pick_frame, text="Cards to pick:").pack(side="left")
            self.pick_var = ctk.StringVar(value=str(card.pick))
            self.pick_menu = ctk.CTkOptionMenu(
                pick_frame,
                values=["1", "2", "3"],
                variable=self.pick_var,
                width=60
            )
            self.pick_menu.pack(side="left", padx=10)
        else:
            self.pick_var = ctk.StringVar(value="1")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save,
            fg_color="#27ae60",
            hover_color="#219a52"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self._delete,
            fg_color="#c0392b",
            hover_color="#a93226"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _save(self):
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Warning", "Text cannot be empty.")
            return

        pick = int(self.pick_var.get())
        self.result = ("save", text, pick)
        self.destroy()

    def _delete(self):
        if messagebox.askyesno("Confirm", "Delete this card?"):
            self.result = ("delete", None, None)
            self.destroy()


class ExportDialog(ctk.CTkToplevel):
    """Dialog to export to PDF."""

    def __init__(self, parent, deck):
        super().__init__(parent)
        self.deck = deck

        self.title("Export PDF")
        self.geometry("400x540")
        self.resizable(False, False)

        ctk.CTkLabel(
            self,
            text="Export Deck to PDF",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)

        # Customization
        ctk.CTkLabel(self, text="Game name:").pack(pady=(10, 5))
        self.name_entry = ctk.CTkEntry(self, width=300)
        self.name_entry.pack()
        self.name_entry.insert(0, deck.config.name)

        ctk.CTkLabel(self, text="Short name:").pack(pady=(10, 5))
        self.short_entry = ctk.CTkEntry(self, width=100)
        self.short_entry.pack()
        self.short_entry.insert(0, deck.config.short_name)

        # Logo for black cards
        ctk.CTkLabel(self, text="Logo for black cards (optional):").pack(pady=(10, 5))
        black_logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        black_logo_frame.pack()

        self.black_logo_path = ctk.StringVar(value=deck.config.black_logo_path or "")
        self.black_logo_entry = ctk.CTkEntry(black_logo_frame, width=220, textvariable=self.black_logo_path)
        self.black_logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            black_logo_frame,
            text="Browse",
            width=70,
            command=lambda: self._browse_logo(self.black_logo_path)
        ).pack(side="left")

        # Logo for white cards
        ctk.CTkLabel(self, text="Logo for white cards (optional):").pack(pady=(10, 5))
        white_logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        white_logo_frame.pack()

        self.white_logo_path = ctk.StringVar(value=deck.config.white_logo_path or "")
        self.white_logo_entry = ctk.CTkEntry(white_logo_frame, width=220, textvariable=self.white_logo_path)
        self.white_logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            white_logo_frame,
            text="Browse",
            width=70,
            command=lambda: self._browse_logo(self.white_logo_path)
        ).pack(side="left")

        # Card type
        ctk.CTkLabel(self, text="Cards to export:").pack(pady=(15, 5))
        self.export_type = ctk.StringVar(value="all")

        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack()

        for text, value in [("All", "all"), ("Black only", "black"), ("White only", "white")]:
            ctk.CTkRadioButton(
                type_frame,
                text=text,
                variable=self.export_type,
                value=value
            ).pack(side="left", padx=10)

        # Export button
        ctk.CTkButton(
            self,
            text="Export PDF",
            command=self._export,
            width=200,
            height=40,
            fg_color="#8e44ad"
        ).pack(pady=25)

        self.grab_set()

    def _browse_logo(self, var: ctk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        if path:
            var.set(path)

    def _export(self):
        # Update config
        self.deck.config.name = self.name_entry.get().strip() or "Cards Against Humanity"
        self.deck.config.short_name = self.short_entry.get().strip()[:5].upper() or "CAH"
        black_logo = self.black_logo_path.get().strip()
        white_logo = self.white_logo_path.get().strip()
        self.deck.config.black_logo_path = black_logo if black_logo and Path(black_logo).exists() else None
        self.deck.config.white_logo_path = white_logo if white_logo and Path(white_logo).exists() else None

        # Output path
        filename = f"{self.deck.config.short_name.lower()}_{self.export_type.get()}.pdf"
        output_path = EXPORTS_DIR / filename

        try:
            export_deck_to_pdf(self.deck, output_path, self.export_type.get())
            self.destroy()
            # Open file manager and select file
            self._reveal_in_file_manager(output_path)
        except Exception as e:
            messagebox.showerror("Error", f"Export error:\n{e}")

    def _reveal_in_file_manager(self, path: Path):
        """Open file manager showing the file."""
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(path)])
            elif system == "Windows":
                subprocess.run(["explorer", "/select,", str(path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(path.parent)])
        except Exception:
            # Fallback: show message with path
            messagebox.showinfo("Success", f"PDF created:\n{path}")


def run_gui():
    """Launch the GUI."""
    app = CAHApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
