"""GUI per il generatore di carte Cards Against Humanity."""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import random
import subprocess
import platform

from .models import CardType, DeckConfig, Card, Deck
from . import db
from .export import export_deck_to_pdf

# Configurazione tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


class CardFrame(ctk.CTkFrame):
    """Frame che rappresenta una carta cliccabile."""

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

        # Header con indice
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
    """Applicazione principale."""

    def __init__(self):
        super().__init__()

        self.title("Cards Against Humanity - Generator")
        self.geometry("1200x800")
        self.minsize(900, 650)

        # Inizializza database
        db.ensure_db()

        # Carica mazzo predefinito o il primo disponibile
        deck_id = db.get_default_deck_id()
        if deck_id:
            self.current_deck = db.get_deck(deck_id)
        else:
            # Crea mazzo vuoto se non esiste
            deck_id = db.create_deck("Cards Against Humanity", "CAH")
            self.current_deck = db.get_deck(deck_id)

        # Paginazione
        self._page = 0
        self._cards_per_page = 30

        self._create_layout()
        self._refresh_cards_view()

    def _create_layout(self):
        """Crea il layout principale."""
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Logo/Titolo
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

        # Statistiche
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=10, pady=5)

        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.stats_label.pack()

        # Pulsanti navigazione
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=20)

        self.btn_black = ctk.CTkButton(
            self.nav_frame,
            text="Carte Nere",
            command=lambda: self._show_cards("black"),
            fg_color="#333333",
            hover_color="#444444"
        )
        self.btn_black.pack(fill="x", pady=5)

        self.btn_white = ctk.CTkButton(
            self.nav_frame,
            text="Carte Bianche",
            command=lambda: self._show_cards("white"),
            fg_color="#e0e0e0",
            text_color="black",
            hover_color="#d0d0d0"
        )
        self.btn_white.pack(fill="x", pady=5)

        self.btn_random = ctk.CTkButton(
            self.nav_frame,
            text="Combo Casuale",
            command=self._show_random_combo,
            fg_color="#c0392b",
            hover_color="#a93226"
        )
        self.btn_random.pack(fill="x", pady=5)

        # Separator
        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=15)

        # Gestione mazzi
        self.deck_label = ctk.CTkLabel(
            self.sidebar,
            text="Mazzi",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.deck_label.pack(pady=(5, 10))

        self.btn_new_deck = ctk.CTkButton(
            self.sidebar,
            text="+ Nuovo Mazzo",
            command=self._create_new_deck,
            width=160
        )
        self.btn_new_deck.pack(pady=5)

        self.btn_load_deck = ctk.CTkButton(
            self.sidebar,
            text="Carica Mazzo",
            command=self._load_deck_dialog,
            width=160,
            fg_color="transparent",
            border_width=1
        )
        self.btn_load_deck.pack(pady=5)

        self.btn_set_default = ctk.CTkButton(
            self.sidebar,
            text="Imposta Predefinito",
            command=self._set_as_default,
            width=160,
            fg_color="transparent",
            border_width=1,
            text_color="gray"
        )
        self.btn_set_default.pack(pady=5)

        self.btn_add_card = ctk.CTkButton(
            self.sidebar,
            text="+ Aggiungi Carta",
            command=self._add_card_dialog,
            width=160,
            fg_color="#27ae60",
            hover_color="#219a52"
        )
        self.btn_add_card.pack(pady=5)

        self.btn_add_batch = ctk.CTkButton(
            self.sidebar,
            text="+ Aggiungi Multiple",
            command=self._add_batch_dialog,
            width=160,
            fg_color="#2980b9",
            hover_color="#2472a4"
        )
        self.btn_add_batch.pack(pady=5)

        # Export in basso
        self.btn_copy_text = ctk.CTkButton(
            self.sidebar,
            text="Copia come Testo",
            command=self._copy_as_text,
            width=160,
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        self.btn_copy_text.pack(side="bottom", pady=(0, 10))

        self.btn_export = ctk.CTkButton(
            self.sidebar,
            text="Esporta PDF",
            command=self._export_pdf,
            width=160,
            height=40,
            fg_color="#8e44ad",
            hover_color="#7d3c98"
        )
        self.btn_export.pack(side="bottom", pady=(0, 10))

        # Area principale
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Header area principale
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Tutte le Carte",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left")

        # Ricerca
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_cards())

        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Cerca...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="right")

        # Area scrollabile per le carte
        self.cards_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.cards_scroll.pack(fill="both", expand=True)

        # Paginazione in basso
        self.pagination_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pagination_frame.pack(fill="x", pady=(10, 0))

        self.btn_prev_page = ctk.CTkButton(
            self.pagination_frame,
            text="← Precedente",
            command=self._prev_page,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.btn_prev_page.pack(side="left")

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Pagina 1/1",
            font=ctk.CTkFont(size=12)
        )
        self.page_label.pack(side="left", expand=True)

        self.btn_next_page = ctk.CTkButton(
            self.pagination_frame,
            text="Successiva →",
            command=self._next_page,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.btn_next_page.pack(side="right")

        # Fix scroll mouse per macOS
        self._setup_mousewheel_scroll()

    def _setup_mousewheel_scroll(self):
        """Configura lo scroll del mouse/trackpad e tastiera."""
        canvas = self.cards_scroll._parent_canvas
        self._scroll_canvas = canvas

        # Scroll con tastiera (funziona sempre)
        self.bind_all("<Up>", lambda e: canvas.yview_scroll(-3, "units"))
        self.bind_all("<Down>", lambda e: canvas.yview_scroll(3, "units"))
        self.bind_all("<Prior>", lambda e: canvas.yview_scroll(-10, "units"))  # Page Up
        self.bind_all("<Next>", lambda e: canvas.yview_scroll(10, "units"))    # Page Down
        self.bind_all("<Home>", lambda e: canvas.yview_moveto(0))
        self.bind_all("<End>", lambda e: canvas.yview_moveto(1))

        # Cambio pagina con frecce sinistra/destra (non in campi testo)
        self.bind_all("<Left>", self._on_left_key)
        self.bind_all("<Right>", self._on_right_key)

        # Mouse wheel - usa Enter/Leave per bind/unbind
        self.cards_scroll.bind("<Enter>", self._on_enter_scroll_area)
        self.cards_scroll.bind("<Leave>", self._on_leave_scroll_area)

    def _on_enter_scroll_area(self, event):
        """Attiva lo scroll quando il mouse entra nell'area."""
        if platform.system() == "Darwin":
            self.bind_all("<MouseWheel>", self._on_mousewheel_mac)
        else:
            self.bind_all("<MouseWheel>", self._on_mousewheel_other)
            self.bind_all("<Button-4>", self._on_scroll_up)
            self.bind_all("<Button-5>", self._on_scroll_down)

    def _on_leave_scroll_area(self, event):
        """Disattiva lo scroll quando il mouse esce dall'area."""
        self.unbind_all("<MouseWheel>")
        if platform.system() != "Darwin":
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")

    def _on_mousewheel_mac(self, event):
        """Scroll su macOS."""
        self._scroll_canvas.yview_scroll(-event.delta, "units")

    def _on_mousewheel_other(self, event):
        """Scroll su Windows/Linux."""
        self._scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _on_scroll_up(self, event):
        self._scroll_canvas.yview_scroll(-3, "units")

    def _on_scroll_down(self, event):
        self._scroll_canvas.yview_scroll(3, "units")

    def _on_left_key(self, event):
        """Pagina precedente se non in campo testo."""
        if not isinstance(event.widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            self._prev_page()

    def _on_right_key(self, event):
        """Pagina successiva se non in campo testo."""
        if not isinstance(event.widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            self._next_page()

    def _refresh_cards_view(self, card_type: str = "all", reset_page: bool = True):
        """Aggiorna la visualizzazione delle carte."""
        # Salva il tipo corrente per refresh successivi
        self._current_view_type = card_type

        # Reset pagina quando cambia vista o ricerca
        if reset_page:
            self._page = 0

        # Pulisci
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        # Seleziona carte
        if card_type == "black":
            all_cards = self.current_deck.black_cards
            self.title_label.configure(text="Carte Nere (Domande)")
        elif card_type == "white":
            all_cards = self.current_deck.white_cards
            self.title_label.configure(text="Carte Bianche (Risposte)")
        else:
            all_cards = self.current_deck.black_cards + self.current_deck.white_cards
            self.title_label.configure(text="Tutte le Carte")

        # Filtra per ricerca
        search_term = self.search_var.get().lower()
        if search_term:
            all_cards = [c for c in all_cards if search_term in c.text.lower()]

        # Calcola paginazione
        total_cards = len(all_cards)
        total_pages = max(1, (total_cards + self._cards_per_page - 1) // self._cards_per_page)
        self._page = min(self._page, total_pages - 1)

        start_idx = self._page * self._cards_per_page
        end_idx = min(start_idx + self._cards_per_page, total_cards)
        cards = all_cards[start_idx:end_idx]

        # Aggiorna paginazione UI
        self.page_label.configure(text=f"Pagina {self._page + 1}/{total_pages} ({total_cards} carte)")
        self.btn_prev_page.configure(state="normal" if self._page > 0 else "disabled")
        self.btn_next_page.configure(state="normal" if self._page < total_pages - 1 else "disabled")

        # Calcola indici base per questa pagina
        # Conta quante carte nere/bianche ci sono prima di questa pagina
        black_before = sum(1 for c in all_cards[:start_idx] if c.card_type == CardType.BLACK)
        white_before = sum(1 for c in all_cards[:start_idx] if c.card_type == CardType.WHITE)

        # Griglia di carte
        cols = 3
        black_idx = black_before
        white_idx = white_before
        for i, card in enumerate(cards):
            row = i // cols
            col = i % cols

            # Indice separato per nere e bianche
            if card.card_type == CardType.BLACK:
                black_idx += 1
                display_idx = black_idx
            else:
                white_idx += 1
                display_idx = white_idx

            card_frame = CardFrame(self.cards_scroll, card, on_click=self._edit_card, index=display_idx)
            card_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Configura griglia
        for i in range(cols):
            self.cards_scroll.columnconfigure(i, weight=1)

        # Scroll in cima
        self.cards_scroll._parent_canvas.yview_moveto(0)

    def _show_cards(self, card_type: str):
        """Mostra carte di un tipo specifico."""
        self._refresh_cards_view(card_type)

    def _prev_page(self):
        """Vai alla pagina precedente."""
        if self._page > 0:
            self._page -= 1
            current_type = getattr(self, '_current_view_type', 'all')
            self._refresh_cards_view(current_type, reset_page=False)

    def _next_page(self):
        """Vai alla pagina successiva."""
        self._page += 1
        current_type = getattr(self, '_current_view_type', 'all')
        self._refresh_cards_view(current_type, reset_page=False)

    def _filter_cards(self):
        """Filtra le carte in base alla ricerca."""
        current_type = getattr(self, '_current_view_type', 'all')
        self._refresh_cards_view(current_type)  # reset_page=True di default

    def _edit_card(self, card: Card):
        """Apre dialog per modificare una carta."""
        dialog = EditCardDialog(self, card)
        self.wait_window(dialog)

        if dialog.result:
            action, new_text, new_pick = dialog.result

            if action == "delete":
                # Rimuovi carta dal database
                if card.id:
                    db.delete_card(card.id)
                # Rimuovi dalla lista locale
                if card.card_type == CardType.BLACK:
                    self.current_deck.black_cards.remove(card)
                else:
                    self.current_deck.white_cards.remove(card)
            elif action == "save":
                # Aggiorna carta nel database
                if card.id:
                    db.update_card(card.id, new_text, new_pick)
                # Aggiorna localmente
                card.text = new_text
                card.pick = new_pick

            self._update_stats()
            current_type = getattr(self, '_current_view_type', 'all')
            self._refresh_cards_view(current_type)

    def _show_random_combo(self):
        """Mostra una combinazione casuale."""
        # Pulisci
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        self.title_label.configure(text="Combinazione Casuale")

        if not self.current_deck.black_cards or not self.current_deck.white_cards:
            ctk.CTkLabel(
                self.cards_scroll,
                text="Servono carte nere e bianche per generare combinazioni",
                text_color="gray"
            ).pack(pady=50)
            return

        black_card = random.choice(self.current_deck.black_cards)
        white_cards = random.sample(
            self.current_deck.white_cards,
            min(black_card.pick, len(self.current_deck.white_cards))
        )

        # Container centrale
        combo_frame = ctk.CTkFrame(self.cards_scroll, fg_color="transparent")
        combo_frame.pack(expand=True, pady=50)

        # Carta nera
        black_frame = CardFrame(combo_frame, black_card, width=250, height=150)
        black_frame.pack(pady=10)

        # Indicatore pick se > 1
        if black_card.pick > 1:
            pick_label = ctk.CTkLabel(
                combo_frame,
                text=f"Pesca {black_card.pick} carte",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            pick_label.pack()

        # Freccia
        arrow = ctk.CTkLabel(combo_frame, text="↓", font=ctk.CTkFont(size=30))
        arrow.pack(pady=5)

        # Carte bianche (numerate se più di una)
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

        # Risultato - costruisci la frase
        result = black_card.text
        blanks_count = result.count("_____")

        if blanks_count >= len(white_cards):
            # Sostituisci i blank con le carte
            for wc in white_cards:
                result = result.replace("_____", f"[{wc.text}]", 1)
        else:
            # Non abbastanza blank, aggiungi le risposte alla fine
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

        # Pulsante refresh
        btn_refresh = ctk.CTkButton(
            combo_frame,
            text="Altra combinazione",
            command=self._show_random_combo,
            fg_color="#c0392b"
        )
        btn_refresh.pack(pady=10)

    def _create_new_deck(self):
        """Apre dialog per creare nuovo mazzo."""
        dialog = NewDeckDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            name, short_name, logo_path, import_default = dialog.result
            # Crea mazzo nel database
            deck_id = db.create_deck(name, short_name, logo_path)

            if import_default:
                # Copia carte dal mazzo predefinito
                default_id = db.get_default_deck_id()
                if default_id and default_id != deck_id:
                    default_deck = db.get_deck(default_id)
                    for card in default_deck.black_cards + default_deck.white_cards:
                        db.add_card(deck_id, card.text, card.card_type, card.pick)

            self.current_deck = db.get_deck(deck_id)
            self._update_stats()
            self._refresh_cards_view()
            messagebox.showinfo("Successo", f"Mazzo '{name}' creato!")

    def _set_as_default(self):
        """Imposta il mazzo corrente come predefinito all'avvio."""
        if self.current_deck and self.current_deck.id:
            db.set_default_deck_id(self.current_deck.id)
            messagebox.showinfo(
                "Predefinito",
                f"'{self.current_deck.config.name}' verrà caricato all'avvio."
            )

    def _load_deck_dialog(self):
        """Apre dialog per caricare un mazzo."""
        decks = db.list_decks()

        if not decks:
            messagebox.showinfo("Info", "Nessun mazzo salvato.")
            return

        dialog = LoadDeckDialog(self, decks)
        self.wait_window(dialog)

        if dialog.result:
            deck_id = dialog.result
            self.current_deck = db.get_deck(deck_id)
            self._update_stats()
            self._refresh_cards_view()

    def _add_card_dialog(self):
        """Apre dialog per aggiungere una carta."""
        dialog = AddCardDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            card_type, text, pick = dialog.result
            # Salva nel database
            card_id = db.add_card(self.current_deck.id, text, card_type, pick)
            # Aggiungi localmente
            card = Card(text=text, card_type=card_type, pick=pick, id=card_id)
            if card_type == CardType.BLACK:
                self.current_deck.black_cards.append(card)
            else:
                self.current_deck.white_cards.append(card)
            self._update_stats()
            self._refresh_cards_view()
            messagebox.showinfo("Successo", "Carta aggiunta!")

    def _add_batch_dialog(self):
        """Apre dialog per aggiungere più carte."""
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
                messagebox.showinfo("Successo", f"{count} carte aggiunte!")

    def _update_stats(self):
        """Aggiorna le statistiche visualizzate."""
        self.stats_label.configure(
            text=f"Carte: {len(self.current_deck.black_cards)} nere, "
                 f"{len(self.current_deck.white_cards)} bianche"
        )

    def _export_pdf(self):
        """Esporta il mazzo in PDF."""
        dialog = ExportDialog(self, self.current_deck)
        self.wait_window(dialog)

    def _copy_as_text(self):
        """Copia il mazzo come testo negli appunti."""
        lines = []
        lines.append(f"# {self.current_deck.config.name}")
        lines.append(f"# Carte nere: {len(self.current_deck.black_cards)}, Carte bianche: {len(self.current_deck.white_cards)}")
        lines.append("")

        lines.append("## CARTE NERE (Domande)")
        lines.append("")
        for i, card in enumerate(self.current_deck.black_cards, 1):
            pick_info = f" [PESCA {card.pick}]" if card.pick > 1 else ""
            lines.append(f"{i}. {card.text}{pick_info}")

        lines.append("")
        lines.append("## CARTE BIANCHE (Risposte)")
        lines.append("")
        for i, card in enumerate(self.current_deck.white_cards, 1):
            lines.append(f"{i}. {card.text}")

        text = "\n".join(lines)

        # Copia negli appunti
        self.clipboard_clear()
        self.clipboard_append(text)

        messagebox.showinfo(
            "Copiato!",
            f"Mazzo copiato negli appunti!\n\n"
            f"{len(self.current_deck.black_cards)} carte nere\n"
            f"{len(self.current_deck.white_cards)} carte bianche"
        )


class NewDeckDialog(ctk.CTkToplevel):
    """Dialog per creare un nuovo mazzo."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Nuovo Mazzo")
        self.geometry("400x400")
        self.resizable(False, False)

        # Campi
        ctk.CTkLabel(self, text="Nome del mazzo:").pack(pady=(20, 5))
        self.name_entry = ctk.CTkEntry(self, width=300)
        self.name_entry.pack()
        self.name_entry.insert(0, "Il mio mazzo")

        ctk.CTkLabel(self, text="Nome breve (max 5 caratteri):").pack(pady=(15, 5))
        self.short_entry = ctk.CTkEntry(self, width=100)
        self.short_entry.pack()
        self.short_entry.insert(0, "MAZZO")

        ctk.CTkLabel(self, text="Logo (opzionale):").pack(pady=(15, 5))
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.pack()

        self.logo_path = ctk.StringVar()
        self.logo_entry = ctk.CTkEntry(self.logo_frame, width=200, textvariable=self.logo_path)
        self.logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            self.logo_frame,
            text="Sfoglia",
            width=80,
            command=self._browse_logo
        ).pack(side="left")

        # Checkbox importa predefinite
        self.import_default = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self,
            text="Importa carte predefinite",
            variable=self.import_default
        ).pack(pady=20)

        # Pulsanti
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Crea", command=self._create).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Annulla",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Immagini", "*.png *.jpg *.jpeg")]
        )
        if path:
            self.logo_path.set(path)

    def _create(self):
        name = self.name_entry.get().strip() or "Il mio mazzo"
        short_name = self.short_entry.get().strip()[:5].upper() or "MAZZO"
        logo = self.logo_path.get() or None

        # Ritorna i parametri invece di creare il deck
        self.result = (name, short_name, logo, self.import_default.get())
        self.destroy()


class LoadDeckDialog(ctk.CTkToplevel):
    """Dialog per caricare un mazzo salvato."""

    def __init__(self, parent, decks: list):
        super().__init__(parent)
        self.result = None
        self.decks = decks

        self.title("Carica Mazzo")
        self.geometry("400x380")
        self.resizable(False, False)

        ctk.CTkLabel(
            self,
            text="Seleziona un mazzo:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=20)

        # Lista mazzi
        self.listbox_frame = ctk.CTkScrollableFrame(self, width=350, height=150)
        self.listbox_frame.pack(pady=10)

        self.selected_idx = ctk.IntVar(value=0)

        for i, deck in enumerate(decks):
            rb = ctk.CTkRadioButton(
                self.listbox_frame,
                text=f"{deck['name']} ({deck['black_count']}N, {deck['white_count']}B)",
                variable=self.selected_idx,
                value=i
            )
            rb.pack(anchor="w", pady=5)

        # Pulsanti
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Carica", command=self._load).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Elimina",
            command=self._delete,
            fg_color="#c0392b"
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Annulla",
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
        if messagebox.askyesno("Conferma", f"Eliminare '{self.decks[idx]['name']}'?"):
            db.delete_deck(self.decks[idx]["id"])
            self.destroy()


class AddCardDialog(ctk.CTkToplevel):
    """Dialog per aggiungere una carta."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Aggiungi Carta")
        self.geometry("400x380")
        self.resizable(False, False)

        # Tipo carta
        ctk.CTkLabel(self, text="Tipo di carta:").pack(pady=(20, 5))

        self.card_type = ctk.StringVar(value="black")
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack()

        ctk.CTkRadioButton(
            type_frame,
            text="Nera (domanda)",
            variable=self.card_type,
            value="black"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            type_frame,
            text="Bianca (risposta)",
            variable=self.card_type,
            value="white"
        ).pack(side="left", padx=10)

        # Testo
        ctk.CTkLabel(self, text="Testo (usa _____ per gli spazi):").pack(pady=(15, 5))
        self.text_entry = ctk.CTkTextbox(self, width=350, height=80)
        self.text_entry.pack()

        # Pick (solo per nere)
        pick_frame = ctk.CTkFrame(self, fg_color="transparent")
        pick_frame.pack(pady=10)

        ctk.CTkLabel(pick_frame, text="Carte da pescare:").pack(side="left")
        self.pick_var = ctk.StringVar(value="1")
        self.pick_menu = ctk.CTkOptionMenu(
            pick_frame,
            values=["1", "2", "3"],
            variable=self.pick_var,
            width=60
        )
        self.pick_menu.pack(side="left", padx=10)

        # Pulsanti
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Aggiungi", command=self._add).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Annulla",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _add(self):
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attenzione", "Inserisci il testo della carta.")
            return

        card_type = CardType.BLACK if self.card_type.get() == "black" else CardType.WHITE
        pick = int(self.pick_var.get())

        self.result = (card_type, text, pick)
        self.destroy()


class BatchAddDialog(ctk.CTkToplevel):
    """Dialog per aggiungere più carte alla volta."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Aggiungi Carte Multiple")
        self.geometry("500x550")
        self.resizable(False, False)

        ctk.CTkLabel(
            self,
            text="Aggiungi più carte (una per riga)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))

        # Carte nere
        black_frame = ctk.CTkFrame(self)
        black_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            black_frame,
            text="Carte Nere (domande):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkLabel(
            black_frame,
            text="Usa _____ per gli spazi vuoti",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w")

        self.black_text = ctk.CTkTextbox(black_frame, width=440, height=120)
        self.black_text.pack(pady=5)
        self.black_text.insert("1.0", "Cosa mi tiene sveglio la notte? _____.\nIl segreto della felicità è _____.")

        # Carte bianche
        white_frame = ctk.CTkFrame(self)
        white_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            white_frame,
            text="Carte Bianche (risposte):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(5, 0))

        self.white_text = ctk.CTkTextbox(white_frame, width=440, height=120)
        self.white_text.pack(pady=5)
        self.white_text.insert("1.0", "Un gatto che giudica\nLa pizza con ananas\nI lunedì mattina")

        # Info
        ctk.CTkLabel(
            self,
            text="Ogni riga diventa una carta separata",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=5)

        # Pulsanti
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="Aggiungi Tutte",
            command=self._add,
            fg_color="#27ae60",
            hover_color="#219a52"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Annulla",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _add(self):
        black_lines = self.black_text.get("1.0", "end").strip().split("\n")
        white_lines = self.white_text.get("1.0", "end").strip().split("\n")

        # Filtra righe vuote
        black_cards = [line for line in black_lines if line.strip()]
        white_cards = [line for line in white_lines if line.strip()]

        if not black_cards and not white_cards:
            messagebox.showwarning("Attenzione", "Inserisci almeno una carta.")
            return

        self.result = (black_cards, white_cards)
        self.destroy()


class EditCardDialog(ctk.CTkToplevel):
    """Dialog per modificare o eliminare una carta."""

    def __init__(self, parent, card: Card):
        super().__init__(parent)
        self.result = None
        self.card = card

        is_black = card.card_type == CardType.BLACK
        title_type = "Nera" if is_black else "Bianca"

        self.title(f"Modifica Carta {title_type}")
        self.geometry("450x350")
        self.resizable(False, False)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="#1a1a1a" if is_black else "#f5f5f5", corner_radius=10)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header_frame,
            text=f"Carta {title_type}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white" if is_black else "black"
        ).pack(pady=10)

        # Testo
        ctk.CTkLabel(self, text="Testo della carta:").pack(pady=(10, 5))
        self.text_entry = ctk.CTkTextbox(self, width=400, height=100)
        self.text_entry.pack()
        self.text_entry.insert("1.0", card.text)

        # Pick (solo per carte nere)
        if is_black:
            pick_frame = ctk.CTkFrame(self, fg_color="transparent")
            pick_frame.pack(pady=10)

            ctk.CTkLabel(pick_frame, text="Carte da pescare:").pack(side="left")
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

        # Pulsanti
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Salva",
            command=self._save,
            fg_color="#27ae60",
            hover_color="#219a52"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Elimina",
            command=self._delete,
            fg_color="#c0392b",
            hover_color="#a93226"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Annulla",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)

        self.grab_set()

    def _save(self):
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attenzione", "Il testo non può essere vuoto.")
            return

        pick = int(self.pick_var.get())
        self.result = ("save", text, pick)
        self.destroy()

    def _delete(self):
        if messagebox.askyesno("Conferma", "Eliminare questa carta?"):
            self.result = ("delete", None, None)
            self.destroy()


class ExportDialog(ctk.CTkToplevel):
    """Dialog per esportare in PDF."""

    def __init__(self, parent, deck):
        super().__init__(parent)
        self.deck = deck

        self.title("Esporta PDF")
        self.geometry("400x480")
        self.resizable(False, False)

        ctk.CTkLabel(
            self,
            text="Esporta Mazzo in PDF",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)

        # Personalizzazione
        ctk.CTkLabel(self, text="Nome del gioco:").pack(pady=(10, 5))
        self.name_entry = ctk.CTkEntry(self, width=300)
        self.name_entry.pack()
        self.name_entry.insert(0, deck.config.name)

        ctk.CTkLabel(self, text="Nome breve:").pack(pady=(10, 5))
        self.short_entry = ctk.CTkEntry(self, width=100)
        self.short_entry.pack()
        self.short_entry.insert(0, deck.config.short_name)

        # Logo
        ctk.CTkLabel(self, text="Logo (opzionale):").pack(pady=(10, 5))
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack()

        self.logo_path = ctk.StringVar(value=deck.config.logo_path or "")
        self.logo_entry = ctk.CTkEntry(logo_frame, width=220, textvariable=self.logo_path)
        self.logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            logo_frame,
            text="Sfoglia",
            width=70,
            command=self._browse_logo
        ).pack(side="left")

        # Tipo carte
        ctk.CTkLabel(self, text="Carte da esportare:").pack(pady=(15, 5))
        self.export_type = ctk.StringVar(value="all")

        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack()

        for text, value in [("Tutte", "all"), ("Solo nere", "black"), ("Solo bianche", "white")]:
            ctk.CTkRadioButton(
                type_frame,
                text=text,
                variable=self.export_type,
                value=value
            ).pack(side="left", padx=10)

        # Pulsante export
        ctk.CTkButton(
            self,
            text="Esporta PDF",
            command=self._export,
            width=200,
            height=40,
            fg_color="#8e44ad"
        ).pack(pady=25)

        self.grab_set()

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Immagini", "*.png *.jpg *.jpeg")]
        )
        if path:
            self.logo_path.set(path)

    def _export(self):
        # Aggiorna config
        self.deck.config.name = self.name_entry.get().strip() or "Cards Against Humanity"
        self.deck.config.short_name = self.short_entry.get().strip()[:5].upper() or "CAH"
        logo = self.logo_path.get().strip()
        self.deck.config.logo_path = logo if logo and Path(logo).exists() else None

        # Percorso output
        filename = f"{self.deck.config.short_name.lower()}_{self.export_type.get()}.pdf"
        output_path = EXPORTS_DIR / filename

        try:
            export_deck_to_pdf(self.deck, output_path, self.export_type.get())
            self.destroy()
            # Apri file manager e seleziona il file
            self._reveal_in_file_manager(output_path)
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'export:\n{e}")

    def _reveal_in_file_manager(self, path: Path):
        """Apre il file manager mostrando il file."""
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(path)])
            elif system == "Windows":
                subprocess.run(["explorer", "/select,", str(path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(path.parent)])
        except Exception:
            # Fallback: mostra messaggio con percorso
            messagebox.showinfo("Successo", f"PDF creato:\n{path}")


def run_gui():
    """Avvia la GUI."""
    app = CAHApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
