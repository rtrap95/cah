"""CLI interattiva per il generatore di carte."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import print as rprint
from pathlib import Path
import random

from .models import CardType, DeckConfig
from .database import create_default_deck, get_cards_count
from .decks import (
    list_saved_decks, save_deck, load_deck, delete_deck,
    create_empty_deck, add_card_to_deck
)
from .export import export_deck_to_pdf

app = typer.Typer(help="Generatore di carte Cards Against Humanity")
console = Console()

EXPORTS_DIR = Path(__file__).parent.parent / "exports"


def ensure_exports_dir():
    """Assicura che la directory exports esista."""
    EXPORTS_DIR.mkdir(exist_ok=True)


@app.command()
def menu():
    """Avvia il menu interattivo principale."""
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold white on black] CARDS AGAINST HUMANITY [/]\n"
            "[dim]Generatore di carte[/]",
            border_style="white"
        ))

        console.print("\n[bold]Menu principale:[/]\n")
        console.print("  [cyan]1.[/] Esplora carte predefinite")
        console.print("  [cyan]2.[/] Crea nuovo mazzo personalizzato")
        console.print("  [cyan]3.[/] Gestisci mazzi salvati")
        console.print("  [cyan]4.[/] Esporta in PDF")
        console.print("  [cyan]5.[/] Genera combinazione casuale")
        console.print("  [cyan]0.[/] Esci\n")

        choice = Prompt.ask("Scegli un'opzione", choices=["0", "1", "2", "3", "4", "5"])

        if choice == "0":
            console.print("\n[dim]Arrivederci![/]")
            break
        elif choice == "1":
            explore_cards()
        elif choice == "2":
            create_custom_deck()
        elif choice == "3":
            manage_decks()
        elif choice == "4":
            export_menu()
        elif choice == "5":
            random_combo()


def explore_cards():
    """Esplora le carte predefinite."""
    deck = create_default_deck()
    stats = get_cards_count()

    while True:
        console.clear()
        console.print(Panel.fit(
            f"[bold]Carte predefinite[/]\n"
            f"Nere: {stats['black']} | Bianche: {stats['white']} | Totale: {stats['total']}",
            border_style="cyan"
        ))

        console.print("\n  [cyan]1.[/] Mostra carte nere (domande)")
        console.print("  [cyan]2.[/] Mostra carte bianche (risposte)")
        console.print("  [cyan]3.[/] Cerca carta")
        console.print("  [cyan]0.[/] Torna al menu\n")

        choice = Prompt.ask("Scegli", choices=["0", "1", "2", "3"])

        if choice == "0":
            break
        elif choice == "1":
            show_cards_list(deck.black_cards, "Carte Nere (Domande)")
        elif choice == "2":
            show_cards_list(deck.white_cards, "Carte Bianche (Risposte)")
        elif choice == "3":
            search_cards(deck)


def show_cards_list(cards: list, title: str):
    """Mostra una lista di carte con paginazione."""
    page_size = 10
    total_pages = (len(cards) + page_size - 1) // page_size
    current_page = 0

    while True:
        console.clear()
        start = current_page * page_size
        end = min(start + page_size, len(cards))

        table = Table(title=f"{title} (Pagina {current_page + 1}/{total_pages})")
        table.add_column("#", style="dim", width=4)
        table.add_column("Testo", style="white")
        if cards and cards[0].card_type == CardType.BLACK:
            table.add_column("Pick", style="cyan", width=6)

        for i, card in enumerate(cards[start:end], start=start + 1):
            if card.card_type == CardType.BLACK:
                table.add_row(str(i), card.text, str(card.pick) if card.pick > 1 else "")
            else:
                table.add_row(str(i), card.text)

        console.print(table)
        console.print(f"\n[dim]< Prec[/] | [dim]Succ >[/] | [dim]Q per uscire[/]")

        key = Prompt.ask("", choices=["<", ">", "q", "Q"], default=">")

        if key in ["q", "Q"]:
            break
        elif key == "<" and current_page > 0:
            current_page -= 1
        elif key == ">" and current_page < total_pages - 1:
            current_page += 1


def search_cards(deck):
    """Cerca carte per testo."""
    console.clear()
    query = Prompt.ask("Cerca").lower()

    results = []
    for card in deck.black_cards + deck.white_cards:
        if query in card.text.lower():
            results.append(card)

    if not results:
        console.print(f"\n[yellow]Nessun risultato per '{query}'[/]")
    else:
        console.print(f"\n[green]Trovate {len(results)} carte:[/]\n")
        for card in results[:20]:
            card_type = "[black on white]BIANCA[/]" if card.card_type == CardType.WHITE else "[white on black]NERA[/]"
            console.print(f"  {card_type} {card.text}")

    Prompt.ask("\n[dim]Premi Invio per continuare[/]")


def create_custom_deck():
    """Crea un nuovo mazzo personalizzato."""
    console.clear()
    console.print(Panel.fit("[bold]Crea nuovo mazzo[/]", border_style="green"))

    name = Prompt.ask("\nNome del mazzo", default="Il mio mazzo")
    short_name = Prompt.ask("Nome breve (max 5 caratteri)", default="MAZZO")[:5].upper()

    logo_path = None
    if Confirm.ask("Vuoi aggiungere un logo?", default=False):
        logo_path = Prompt.ask("Percorso del logo (PNG/JPG)")
        if not Path(logo_path).exists():
            console.print("[yellow]File non trovato, continuo senza logo[/]")
            logo_path = None

    deck = create_empty_deck(name, short_name, logo_path)

    # Chiedi se importare carte predefinite
    if Confirm.ask("\nVuoi importare le carte predefinite?", default=True):
        default_deck = create_default_deck()
        deck.black_cards = list(default_deck.black_cards)
        deck.white_cards = list(default_deck.white_cards)
        console.print(f"[green]Importate {deck.total_cards} carte![/]")

    # Menu aggiunta carte
    while True:
        console.print(f"\n[dim]Carte attuali: {len(deck.black_cards)} nere, {len(deck.white_cards)} bianche[/]")
        console.print("\n  [cyan]1.[/] Aggiungi carta nera")
        console.print("  [cyan]2.[/] Aggiungi carta bianca")
        console.print("  [cyan]3.[/] Salva mazzo")
        console.print("  [cyan]0.[/] Annulla\n")

        choice = Prompt.ask("Scegli", choices=["0", "1", "2", "3"])

        if choice == "0":
            if deck.total_cards > 0 and Confirm.ask("Vuoi salvare prima di uscire?"):
                filename = save_deck(deck)
                console.print(f"[green]Salvato in {filename}[/]")
            break
        elif choice == "1":
            text = Prompt.ask("Testo (usa _____ per gli spazi)")
            pick = IntPrompt.ask("Quante carte pescare?", default=1)
            add_card_to_deck(deck, text, CardType.BLACK, pick)
            console.print("[green]Carta aggiunta![/]")
        elif choice == "2":
            text = Prompt.ask("Testo della carta bianca")
            add_card_to_deck(deck, text, CardType.WHITE)
            console.print("[green]Carta aggiunta![/]")
        elif choice == "3":
            filename = save_deck(deck)
            console.print(f"[green]Salvato in {filename}[/]")
            break


def manage_decks():
    """Gestisce i mazzi salvati."""
    while True:
        console.clear()
        decks = list_saved_decks()

        console.print(Panel.fit("[bold]Mazzi salvati[/]", border_style="magenta"))

        if not decks:
            console.print("\n[dim]Nessun mazzo salvato[/]")
        else:
            table = Table()
            table.add_column("#", style="dim", width=4)
            table.add_column("Nome")
            table.add_column("Sigla", style="cyan")
            table.add_column("Nere", style="white on black")
            table.add_column("Bianche", style="black on white")

            for i, d in enumerate(decks, 1):
                table.add_row(
                    str(i), d["name"], d["short_name"],
                    str(d["black_count"]), str(d["white_count"])
                )

            console.print(table)

        console.print("\n  [cyan]V.[/] Visualizza mazzo")
        console.print("  [cyan]E.[/] Elimina mazzo")
        console.print("  [cyan]0.[/] Torna al menu\n")

        choice = Prompt.ask("Scegli", choices=["0", "v", "V", "e", "E"])

        if choice == "0":
            break
        elif choice.lower() == "v" and decks:
            idx = IntPrompt.ask("Numero mazzo", default=1) - 1
            if 0 <= idx < len(decks):
                view_deck(decks[idx]["filename"])
        elif choice.lower() == "e" and decks:
            idx = IntPrompt.ask("Numero mazzo da eliminare", default=1) - 1
            if 0 <= idx < len(decks):
                if Confirm.ask(f"Eliminare '{decks[idx]['name']}'?"):
                    delete_deck(decks[idx]["filename"])
                    console.print("[green]Eliminato![/]")


def view_deck(filename: str):
    """Visualizza i dettagli di un mazzo."""
    deck = load_deck(filename)

    console.clear()
    console.print(Panel.fit(
        f"[bold]{deck.config.name}[/] ({deck.config.short_name})\n"
        f"Nere: {len(deck.black_cards)} | Bianche: {len(deck.white_cards)}",
        border_style="cyan"
    ))

    console.print("\n  [cyan]1.[/] Mostra carte nere")
    console.print("  [cyan]2.[/] Mostra carte bianche")
    console.print("  [cyan]0.[/] Torna indietro\n")

    choice = Prompt.ask("Scegli", choices=["0", "1", "2"])

    if choice == "1":
        show_cards_list(deck.black_cards, "Carte Nere")
    elif choice == "2":
        show_cards_list(deck.white_cards, "Carte Bianche")


def export_menu():
    """Menu per l'export in PDF."""
    console.clear()
    console.print(Panel.fit("[bold]Esporta in PDF[/]", border_style="yellow"))

    console.print("\n  [cyan]1.[/] Esporta carte predefinite")
    console.print("  [cyan]2.[/] Esporta mazzo salvato")
    console.print("  [cyan]0.[/] Torna al menu\n")

    choice = Prompt.ask("Scegli", choices=["0", "1", "2"])

    if choice == "0":
        return

    if choice == "1":
        # Configurazione personalizzata
        console.print("\n[bold]Personalizzazione:[/]")
        name = Prompt.ask("Nome del gioco", default="Cards Against Humanity")
        short_name = Prompt.ask("Nome breve", default="CAH")[:5].upper()

        logo_path = None
        if Confirm.ask("Vuoi aggiungere un logo?", default=False):
            logo_path = Prompt.ask("Percorso del logo")
            if not Path(logo_path).exists():
                console.print("[yellow]File non trovato[/]")
                logo_path = None

        config = DeckConfig(name=name, short_name=short_name, logo_path=logo_path)
        deck = create_default_deck(config)
    else:
        decks = list_saved_decks()
        if not decks:
            console.print("[yellow]Nessun mazzo salvato[/]")
            Prompt.ask("[dim]Premi Invio[/]")
            return

        for i, d in enumerate(decks, 1):
            console.print(f"  {i}. {d['name']}")

        idx = IntPrompt.ask("Numero mazzo", default=1) - 1
        if not (0 <= idx < len(decks)):
            return

        deck = load_deck(decks[idx]["filename"])

    # Tipo di carte da esportare
    console.print("\n[bold]Quali carte esportare?[/]")
    console.print("  [cyan]1.[/] Tutte")
    console.print("  [cyan]2.[/] Solo nere")
    console.print("  [cyan]3.[/] Solo bianche\n")

    cards_choice = Prompt.ask("Scegli", choices=["1", "2", "3"])
    cards_type = {"1": "all", "2": "black", "3": "white"}[cards_choice]

    # Export
    ensure_exports_dir()
    filename = f"{deck.config.short_name.lower()}_{cards_type}.pdf"
    output_path = EXPORTS_DIR / filename

    with console.status("[bold green]Generando PDF..."):
        export_deck_to_pdf(deck, output_path, cards_type)

    console.print(f"\n[green]PDF creato: {output_path}[/]")
    Prompt.ask("[dim]Premi Invio per continuare[/]")


def random_combo():
    """Genera una combinazione casuale di carte."""
    deck = create_default_deck()

    console.clear()
    console.print(Panel.fit("[bold]Combinazione casuale[/]", border_style="red"))

    black_card = random.choice(deck.black_cards)
    white_cards = random.sample(deck.white_cards, min(black_card.pick, len(deck.white_cards)))

    console.print("\n[white on black] DOMANDA [/]")
    console.print(f"\n  {black_card.text}\n")

    console.print("[black on white] RISPOSTA [/]")
    for card in white_cards:
        console.print(f"\n  {card.text}")

    # Mostra il risultato combinato
    result = black_card.text
    for wc in white_cards:
        result = result.replace("_____", f"[bold red]{wc.text}[/]", 1)

    console.print("\n" + "─" * 40)
    console.print(f"\n[italic]{result}[/]")

    console.print("\n")
    if Confirm.ask("Altra combinazione?", default=True):
        random_combo()


def main():
    """Entry point principale."""
    app()


if __name__ == "__main__":
    main()
